"""
Piecemint MCP server — stdio transport, shares the same SQLite DB as FastAPI.
  
Run (from repo / Cursor MCP config):
  cd piecemint/backend && pipenv run python mcp_server.py

Tools scope to the single built-in org; the `tenant` argument accepts id, legacy ids
(tenant_a, tenant_b), or the org display name.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager

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
from api.tenant_query import resolve_tenant_id

_INVOICE_GEN = os.path.join(_BACKEND_ROOT, "plugins", "invoice_gen")
if _INVOICE_GEN not in sys.path:
    sys.path.insert(0, _INVOICE_GEN)
from builders import render_invoice  # noqa: E402
from schemas import InvoiceExportConfig  # noqa: E402

# Initialize schema + seed (idempotent) before first tool use
init_db()
_db0 = SessionLocal()
try:
    ensure_seed_data(_db0)
finally:
    _db0.close()

mcp = FastMCP(
    "Piecemint",
    instructions="Read and modify Piecemint data (single org). list_tenants returns the org id and name. Tool `tenant` args accept id, legacy names, or org display name. Email: send_email (plain text) and send_invoice_email (PDF/XLSX/DOCX attachment) use the same SMTP as the app (Email notifications / FF_SMTP_*).",
)


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
def list_tenants() -> str:
    """List all tenant ids and display names in the database."""
    with session_scope() as db:
        rows = db.query(db_models.Tenant).order_by(db_models.Tenant.id).all()
        data = [{"id": t.id, "name": t.name} for t in rows]
    return json.dumps(data, indent=2)


@mcp.tool()
def get_clients(tenant: str) -> str:
    """List clients. `tenant` may be org id, legacy id (tenant_a / tenant_b), or display name."""
    with session_scope() as db:
        tid = resolve_tenant_id(db, tenant)
        if not tid:
            return json.dumps({"error": f"Unknown tenant: {tenant!r}"})
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
def get_stockholders(tenant: str) -> str:
    """List stockholders for a tenant (by id or name)."""
    with session_scope() as db:
        tid = resolve_tenant_id(db, tenant)
        if not tid:
            return json.dumps({"error": f"Unknown tenant: {tenant!r}"})
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
    tenant: str,
    name: str,
    email: str = "",
    share_percent: float | None = None,
    notes: str = "",
) -> str:
    """
    Add a stockholder to a tenant. Example: add_stockholder(
        tenant='Acme Corp', name='Alex Founder', email='alex@example.com', share_percent=5.0
    )
    """
    with session_scope() as db:
        tid = resolve_tenant_id(db, tenant)
        if not tid:
            return json.dumps({"ok": False, "error": f"Unknown tenant: {tenant!r}"})
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
            "tenant_id": tid,
            "name": sh.name,
            "email": sh.email,
            "share_percent": float(sh.share_percent) if sh.share_percent is not None else None,
        }
    return json.dumps({"ok": True, "stockholder": row}, indent=2)


@mcp.tool()
def list_transactions(tenant: str, limit: int = 50) -> str:
    """Recent transactions for a tenant (by id or name)."""
    with session_scope() as db:
        tid = resolve_tenant_id(db, tenant)
        if not tid:
            return json.dumps({"error": f"Unknown tenant: {tenant!r}"})
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
                "is_recurring": t.is_recurring,
            }
            for t in rows
        ]
    return json.dumps(out, indent=2)


def _split_recipients(to_field: str) -> list[str]:
    return [x.strip() for x in to_field.replace(";", ",").split(",") if x.strip()]


@mcp.tool()
def send_email(tenant: str, to: str, subject: str, text_body: str) -> str:
    """
    Send a plain-text email using the same SMTP settings as the app (Email notifications plugin or FF_SMTP_*).
    `to` may be a single address or comma/semicolon-separated list.
    """
    with session_scope() as db:
        tid = resolve_tenant_id(db, tenant)
        if not tid:
            return json.dumps({"ok": False, "error": f"Unknown tenant: {tenant!r}"})
    addrs = _split_recipients(to)
    if not addrs:
        return json.dumps({"ok": False, "error": "No recipient addresses in `to`."})
    if not smtp_is_configured(tid):
        return json.dumps(
            {
                "ok": False,
                "error": "SMTP is not configured. Save settings in Email notifications or set FF_SMTP_* on the server.",
            }
        )
    try:
        send_plain_email(tid, addrs, subject, text_body)
    except SmtpSendError as e:
        return json.dumps({"ok": False, "error": str(e)})
    return json.dumps({"ok": True, "to": addrs, "subject": subject.strip() or "(no subject)"}, indent=2)


@mcp.tool()
def send_invoice_email(
    tenant: str,
    client_id: str,
    to: str | None = None,
    subject: str | None = None,
    text_body: str | None = None,
    config_json: str | None = None,
) -> str:
    """
    Build the same invoice file the app would (PDF/XLSX/DOCX from settings) and email it as an attachment.
    Recipient defaults to the client's stored email if `to` is omitted.
    Optional `config_json`: full invoice export JSON (output_format, invoice_document, colors, etc.) as a string;
    if omitted, uses default export settings (same as legacy GET /invoice_gen/generate/:id).
    """
    with session_scope() as db:
        tid = resolve_tenant_id(db, tenant)
        if not tid:
            return json.dumps({"ok": False, "error": f"Unknown tenant: {tenant!r}"})
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

    to_addr = (to or "").strip() or ((c.email or "").strip() if c else "") or None
    if not to_addr:
        return json.dumps(
            {
                "ok": False,
                "error": "No recipient: set `to` or add an email on the client record.",
            }
        )

    if config_json and config_json.strip():
        try:
            cfg = InvoiceExportConfig.model_validate_json(config_json.strip())
        except Exception as e:
            return json.dumps({"ok": False, "error": f"Invalid config_json: {e}"})
    else:
        cfg = InvoiceExportConfig()

    if not smtp_is_configured(tid):
        return json.dumps(
            {
                "ok": False,
                "error": "SMTP is not configured. Save settings in Email notifications or set FF_SMTP_* on the server.",
            }
        )

    content, media_type, ext = render_invoice(
        c.name,
        c.email,
        c.id,
        float(c.total_billed),
        cfg,
    )
    doc = cfg.invoice_document
    inv = (doc.invoice_number or "").strip() if doc else ""
    default_subj = f"Invoice {inv}" if inv else f"Invoice — {c.name}"
    subj = (subject or "").strip() or default_subj
    default_body = (
        f"Hello,\n\nPlease find your invoice attached.\n\nThank you,\n{c.name} (via Piecemint)\n"
    )
    body = (text_body or "").strip() or default_body
    safe_id = "".join(ch for ch in c.id if ch.isalnum() or ch in "-_")[:40] or "client"
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


if __name__ == "__main__":
    mcp.run()
