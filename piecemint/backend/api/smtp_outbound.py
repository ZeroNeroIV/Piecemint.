"""
Shared outbound SMTP for plugins, REST, and MCP.

Settings file stays under plugins/email_notifications/data/ (same as before).
"""

from __future__ import annotations

import json
import os
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "plugins" / "email_notifications" / "data"
_DATA_FILE = _DATA_DIR / "smtp_settings.json"

_ORG_FK_KEY_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class SmtpSendError(Exception):
    """Non-HTTP exception for MCP and internal callers."""


def _sanitize_org_row_id(org_row_id: str) -> str:
    t = str(org_row_id).strip()
    if not _ORG_FK_KEY_RE.match(t):
        raise ValueError("Invalid org workspace key.")
    return t


def _load_all() -> dict:
    if not _DATA_FILE.exists():
        return {}
    try:
        raw = _DATA_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}
        if "default" not in data and "tenant_a" in data and isinstance(data.get("tenant_a"), dict):
            data = {**data, "default": data["tenant_a"]}
        return data
    except (OSError, json.JSONDecodeError):
        return {}


def _save_all(data: dict) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def env_smtp() -> dict:
    try:
        port = int(os.environ.get("FF_SMTP_PORT", "587") or 587)
    except ValueError:
        port = 587
    return {
        "host": os.environ.get("FF_SMTP_HOST", "").strip(),
        "port": port,
        "user": os.environ.get("FF_SMTP_USER", "").strip(),
        "password": (os.environ.get("FF_SMTP_PASSWORD") or "").strip() or None,
        "from_address": (os.environ.get("FF_SMTP_FROM") or os.environ.get("FF_SMTP_USER", "")).strip(),
        "use_tls": os.environ.get("FF_SMTP_USE_TLS", "1").lower() in ("1", "true", "yes", "on"),
    }


def _smtp_saved_row(org_row_id: str) -> dict | None:
    tid = _sanitize_org_row_id(org_row_id)
    row = _load_all().get(tid)
    if not row or not isinstance(row, dict):
        return None
    return row


def effective_smtp(org_row_id: str) -> tuple[str, int, str, str | None, str, bool]:
    env = env_smtp()
    t = _smtp_saved_row(org_row_id)
    if t and (t.get("host") or "").strip():
        port = t.get("port", 587)
        try:
            port = int(port)
        except (TypeError, ValueError):
            port = 587
        pw = (t.get("password") or "").strip() or None
        if not pw:
            pw = env["password"]
        from_addr = (t.get("from_address") or "").strip() or (t.get("user") or "").strip() or env["from_address"]
        return (
            (t.get("host") or "").strip(),
            port,
            (t.get("user") or "").strip(),
            pw,
            from_addr,
            bool(t.get("use_tls", env["use_tls"])),
        )
    return (
        env["host"],
        int(env["port"]),
        env["user"],
        env["password"],
        env["from_address"] or env["user"],
        bool(env["use_tls"]),
    )


def smtp_is_configured(org_row_id: str) -> bool:
    host, _p, user, pw, from_addr, _t = effective_smtp(org_row_id)
    return bool(host and user and pw and from_addr)


def _send_message(msg: EmailMessage, org_row_id: str) -> None:
    if not smtp_is_configured(org_row_id):
        raise SmtpSendError(
            "SMTP is not configured. Save settings in Email notifications or set FF_SMTP_* on the server."
        )
    host, port, user, password, from_addr, use_tls = effective_smtp(org_row_id)
    if not password:
        raise SmtpSendError("No SMTP password configured.")
    if "From" not in msg:
        msg["From"] = from_addr
    try:
        # Port 465 is typically implicit TLS (SMTP_SSL), not STARTTLS on plain SMTP().
        if use_tls and port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
                smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                if use_tls:
                    smtp.starttls()
                smtp.login(user, password)
                smtp.send_message(msg)
    except OSError as e:
        raise SmtpSendError(f"SMTP connection failed: {e}") from e
    except smtplib.SMTPException as e:
        raise SmtpSendError(f"SMTP error: {e}") from e
    except Exception as e:
        raise SmtpSendError(f"SMTP error: {e}") from e


def send_plain_email(org_row_id: str, to_addresses: list[str], subject: str, text_body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject.strip() or "(no subject)"
    msg["To"] = ", ".join(to_addresses)
    msg.set_content(text_body)
    _send_message(msg, org_row_id)


def send_email_with_attachments(
    org_row_id: str,
    to_addresses: list[str],
    subject: str,
    text_body: str,
    attachments: list[tuple[str, bytes, str]],
) -> None:
    """
    attachments: list of (filename, raw_bytes, mime_type e.g. application/pdf)
      For multiple attachments, multipart/mixed is used.
    """
    msg = EmailMessage()
    msg["Subject"] = subject.strip() or "(no subject)"
    msg["To"] = ", ".join(to_addresses)
    msg.set_content(text_body)

    for filename, content, mime in attachments:
        maintype, _, subtype = mime.partition("/")
        st = subtype or "octet-stream"
        mt = maintype or "application"
        msg.add_attachment(content, maintype=mt, subtype=st, filename=filename)

    _send_message(msg, org_row_id)


# ---- persistence API used by email_notifications plugin ----


def load_smtp_settings_store() -> dict:
    return _load_all()


def save_smtp_settings_store(data: dict) -> None:
    _save_all(data)


def smtp_settings_path() -> Path:
    return _DATA_FILE
