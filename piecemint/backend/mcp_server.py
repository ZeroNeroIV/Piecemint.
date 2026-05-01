"""
Piecemint MCP server — stdio transport, shares the same SQLite DB as FastAPI.

Run (from repo / Cursor MCP config):
  cd piecemint/backend && pipenv run python mcp_server.py

Tools scope to this deployment's single workspace (one org row); no tenant selection.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from typing import Any

# Ensure `api` package is importable when run as a script
_BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session

from api import db_models
from api.database import SessionLocal, init_db
from api.seed import ensure_seed_data
from api.smtp_outbound import SmtpSendError, send_email_with_attachments, send_plain_email, smtp_is_configured
from api.workspace_data import primary_org_fk
from plugin_manager import PluginManager


def _plugin_path(plugin_id: str) -> str:
    return os.path.join(_BACKEND_ROOT, "plugins", plugin_id)


def _email_notifications_plugin_present() -> bool:
    return os.path.isfile(os.path.join(_plugin_path("email_notifications"), "manifest.yaml"))


def _smtp_not_configured_message() -> str:
    msg = (
        "SMTP is not configured. Save settings via the Email notifications plugin "
        "or set FF_SMTP_* on the server environment."
    )
    if not _email_notifications_plugin_present():
        return (
            f"{msg} "
            "(The email_notifications folder is missing from plugins/: use FF_SMTP_* for SMTP, "
            "or add the plugin to save settings from the Piecemint UI.)"
        )
    return msg


def _try_load_invoice_gen() -> tuple[Any, Any]:
    """Load invoice builders when invoice_gen plugin is installed; otherwise (None, None)."""
    d = _plugin_path("invoice_gen")
    if (
        not os.path.isdir(d)
        or not os.path.isfile(os.path.join(d, "builders.py"))
        or not os.path.isfile(os.path.join(d, "schemas.py"))
        or not os.path.isfile(os.path.join(d, "invoice_document_render.py"))
    ):
        return None, None
    if d not in sys.path:
        sys.path.insert(0, d)
    try:
        from builders import render_invoice as _ri  # noqa: E402
        from schemas import InvoiceExportConfig as _iec  # noqa: E402

        return _ri, _iec
    except ImportError:
        return None, None


_render_invoice, _InvoiceExportConfig = _try_load_invoice_gen()

# Initialize schema + seed (idempotent) before first tool use
init_db()
_db0 = SessionLocal()
try:
    ensure_seed_data(_db0)
finally:
    _db0.close()


def _mcp_instructions() -> str:
    parts = [
        "Read and modify Piecemint data for one self-hosted workspace.",
        "send_email sends plain-text mail when SMTP is configured (saved in Email notifications plugin "
        "and/or FF_SMTP_* on the MCP host — same SQLite DB directory as Piecemint backend).",
    ]
    if _render_invoice is not None and _InvoiceExportConfig is not None:
        parts.append(
            "send_invoice_email builds an invoice (PDF/XLSX/DOCX) with invoice_gen and emails it "
            "as an attachment when SMTP is configured."
        )
    else:
        parts.append(
            "send_invoice_email returns guidance until invoice_gen exists under backend/plugins/invoice_gen "
            "(then restart MCP)."
        )
    parts.append("Use email_and_invoice_capabilities to see if SMTP and invoice_gen are ready.")
    parts.append("Plugins may add tools via plugins/<id>/mcp_extras.py (register_mcp).")
    return " ".join(parts)


mcp = FastMCP("Piecemint", instructions=_mcp_instructions())

# Filled at import time after built-in tools via PluginManager.apply_mcp_extras.
_PLUGIN_MCP_EXTRAS_LOADED: list[str] = []


@contextmanager
def session_scope() -> Session:
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@mcp.tool()
def get_clients() -> str:
    """List clients in the workspace."""
    with session_scope() as db:
        tid = primary_org_fk(db)
        if not tid:
            return json.dumps({"error": "No workspace org row — seed or migrate the database."})
        clients = (
            db.query(db_models.Client)
            .filter(db_models.Client.tenant_id == tid)
            .order_by(db_models.Client.name)
            .all()
        )
        out = [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "total_billed": c.total_billed,
            }
            for c in clients
        ]
    return json.dumps(out, indent=2)


@mcp.tool()
def get_stockholders() -> str:
    """List stockholders."""
    with session_scope() as db:
        tid = primary_org_fk(db)
        if not tid:
            return json.dumps({"error": "No workspace org row — seed or migrate the database."})
        rows = (
            db.query(db_models.Stockholder)
            .filter(db_models.Stockholder.tenant_id == tid)
            .order_by(db_models.Stockholder.name)
            .all()
        )
        out = [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "share_percent": float(s.share_percent) if s.share_percent is not None else None,
                "notes": s.notes,
            }
            for s in rows
        ]
    return json.dumps(out, indent=2)


@mcp.tool()
def add_stockholder(
    name: str,
    email: str = "",
    share_percent: float | None = None,
    notes: str = "",
) -> str:
    """Add a stockholder. Example: add_stockholder(name='Alex Founder', email='alex@example.com', share_percent=5.0)"""
    with session_scope() as db:
        tid = primary_org_fk(db)
        if not tid:
            return json.dumps({"ok": False, "error": "No workspace org row."})
        sh = db_models.Stockholder(
            tenant_id=tid,
            name=name,
            email=email,
            share_percent=share_percent,
            notes=notes,
        )
        db.add(sh)
        db.flush()
        row = {
            "id": sh.id,
            "workspace_org_id": tid,
            "name": sh.name,
            "email": sh.email,
            "share_percent": float(sh.share_percent) if sh.share_percent is not None else None,
        }
    return json.dumps({"ok": True, "stockholder": row}, indent=2)


@mcp.tool()
def list_transactions(limit: int = 50) -> str:
    """Recent transactions."""
    with session_scope() as db:
        tid = primary_org_fk(db)
        if not tid:
            return json.dumps({"error": "No workspace org row — seed or migrate the database."})
        rows = (
            db.query(db_models.Transaction)
            .filter(db_models.Transaction.tenant_id == tid)
            .order_by(db_models.Transaction.date.desc())
            .limit(max(1, min(limit, 200)))
            .all()
        )
        out = [
            {
                "id": t.id,
                "amount": t.amount,
                "date": t.date,
                "type": t.type,
                "category": t.category,
                "notes": t.notes or "",
                "is_recurring": t.is_recurring,
            }
            for t in rows
        ]
    return json.dumps(out, indent=2)


def _split_recipients(to_field: str) -> list[str]:
    return [x.strip() for x in to_field.replace(";", ",").split(",") if x.strip()]


@mcp.tool()
def email_and_invoice_capabilities() -> str:
    """
    Whether outbound email and invoice-email tools can succeed in this process: SMTP for the workspace,
    invoice_gen plugin loaded, and Email notifications plugin folder present.
    """
    with session_scope() as db:
        tid = primary_org_fk(db)
        smtp = bool(tid and smtp_is_configured(tid))
    return json.dumps(
        {
            "smtp_ready": smtp,
            "invoice_gen_loaded": _render_invoice is not None,
            "email_notifications_plugin_present": _email_notifications_plugin_present(),
            "plugin_mcp_extras_loaded": list(_PLUGIN_MCP_EXTRAS_LOADED),
            "tools": {
                "send_email": {"available": True, "requires_smtp": True},
                "send_invoice_email": {
                    "available": _render_invoice is not None,
                    "requires_smtp": True,
                    "requires_invoice_gen": True,
                },
            },
        },
        indent=2,
    )


@mcp.tool()
def send_email(to: str, subject: str, text_body: str) -> str:
    """
    Send plain-text email via SMTP. Uses the same outbound settings as Piecemint (plugins/email_notifications
    data/smtp_settings.json when that plugin exists, plus FF_* env fallbacks).

    Requires SMTP to be configured; `to` may be comma/semicolon-separated addresses.
    """
    with session_scope() as db:
        tid = primary_org_fk(db)
        if not tid:
            return json.dumps({"ok": False, "error": "No workspace org row."})
    addrs = _split_recipients(to)
    if not addrs:
        return json.dumps({"ok": False, "error": "No recipient addresses in `to`."})
    if not smtp_is_configured(tid):
        return json.dumps({"ok": False, "error": _smtp_not_configured_message()})
    try:
        send_plain_email(tid, addrs, subject, text_body)
    except SmtpSendError as e:
        return json.dumps({"ok": False, "error": str(e)})
    return json.dumps({"ok": True, "to": addrs, "subject": subject.strip() or "(no subject)"}, indent=2)


@mcp.tool()
def send_invoice_email(
    client_id: str,
    to: str | None = None,
    subject: str | None = None,
    text_body: str | None = None,
    config_json: str | None = None,
) -> str:
    """
    Requires plugins/invoice_gen and configured SMTP.

    Builds the same invoice file the Piecemint app would (PDF/XLSX/DOCX) and emails it as an attachment.
    Recipient defaults to the client's stored email if `to` is omitted.
    Optional `config_json`: full invoice export JSON (output_format, invoice_document, colors, etc.);
    if omitted, uses defaults (same as GET /invoice_gen/generate/:id).
    """
    if _render_invoice is None or _InvoiceExportConfig is None:
        return json.dumps(
            {
                "ok": False,
                "error": (
                    "invoice_gen plugin is not installed or failed to load. "
                    "Install piecemint/backend/plugins/invoice_gen and restart mcp_server."
                ),
            }
        )

    with session_scope() as db:
        tid = primary_org_fk(db)
        if not tid:
            return json.dumps({"ok": False, "error": "No workspace org row."})
        c = (
            db.query(db_models.Client)
            .filter(
                db_models.Client.id == client_id,
                db_models.Client.tenant_id == tid,
            )
            .first()
        )
        if not c:
            return json.dumps({"ok": False, "error": f"Client not found: {client_id!r}"})
        # Read columns while Session is active (DetachedInstanceError if accessed after context exit).
        client_name = c.name
        client_email = c.email or ""
        client_row_id = c.id
        client_total_billed = float(c.total_billed)

    to_addr = (to or "").strip() or (client_email.strip() if client_email else "") or None
    if not to_addr:
        return json.dumps(
            {
                "ok": False,
                "error": "No recipient: set `to` or add an email on the client record.",
            }
        )

    if config_json and config_json.strip():
        try:
            cfg = _InvoiceExportConfig.model_validate_json(config_json.strip())
        except Exception as e:
            return json.dumps({"ok": False, "error": f"Invalid config_json: {e}"})
    else:
        cfg = _InvoiceExportConfig()

    if not smtp_is_configured(tid):
        return json.dumps({"ok": False, "error": _smtp_not_configured_message()})

    content, media_type, ext = _render_invoice(
        client_name,
        client_email,
        client_row_id,
        client_total_billed,
        cfg,
    )
    doc = cfg.invoice_document
    inv = (doc.invoice_number or "").strip() if doc else ""
    default_subj = f"Invoice {inv}" if inv else f"Invoice — {client_name}"
    subj = (subject or "").strip() or default_subj
    default_body = (
        f"Hello,\n\nPlease find your invoice attached.\n\nThank you,\n{client_name} (via Piecemint)\n"
    )
    body = (text_body or "").strip() or default_body
    safe_id = "".join(ch for ch in client_row_id if ch.isalnum() or ch in "-_")[:40] or "client"
    filename = f"invoice_{safe_id}{ext}"

    try:
        send_email_with_attachments(
            tid,
            [to_addr],
            subj,
            body,
            [(filename, content, media_type)],
        )
    except SmtpSendError as e:
        return json.dumps({"ok": False, "error": str(e)})

    return json.dumps(
        {"ok": True, "to": to_addr, "subject": subj, "filename": filename},
        indent=2,
    )


_PLUGIN_MCP_EXTRAS_LOADED.extend(PluginManager().apply_mcp_extras(mcp))


if __name__ == "__main__":
    mcp.run()
