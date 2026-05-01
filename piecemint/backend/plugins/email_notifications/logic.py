"""
SMTP: save settings via PUT /email_notifications/config (plugins/.../data/)
or use FF_SMTP_* on the API host (fallback for password when not re-saved).
"""

import logging
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from api.deps import WorkspaceScopeId
from api.models import EmailNotificationTestBody
from api.smtp_outbound import (
    effective_smtp,
    env_smtp,
    load_smtp_settings_store,
    save_smtp_settings_store,
    send_plain_email,
    smtp_is_configured,
)
from api.smtp_outbound import SmtpSendError

router = APIRouter()

log = logging.getLogger(__name__)

_ORG_FK_KEY_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def _sanitize_org_row_id(org_row_id: str) -> str:
    t = str(org_row_id).strip()
    if not _ORG_FK_KEY_RE.match(t):
        raise HTTPException(status_code=400, detail="Invalid workspace org key.")
    return t


def _saved_smtp_row(org_row_id: str) -> dict | None:
    tid = _sanitize_org_row_id(org_row_id)
    row = load_smtp_settings_store().get(tid)
    if not row or not isinstance(row, dict):
        return None
    return row


def _smtp_ready(org_row_id: str) -> bool:
    return smtp_is_configured(org_row_id)


class SmtpConfigOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    host: str | None = None
    port: int = 587
    user: str | None = None
    from_address: str | None = None
    use_tls: bool = True
    has_password: bool = False
    source: str  # "saved" | "env"


class SmtpConfigIn(BaseModel):
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(587, ge=1, le=65535)
    user: str = Field(..., min_length=1, max_length=255)
    from_address: str = Field(..., min_length=1, max_length=255)
    use_tls: bool = True
    password: str | None = Field(None, max_length=2048)

    @field_validator("password", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v


@router.get("/email_notifications/status")
def email_status(org_row_id: WorkspaceScopeId):
    host, port, user, _pw, f, use_tls = effective_smtp(org_row_id)
    t = _saved_smtp_row(org_row_id)
    source = "saved" if (t and (t.get("host") or "").strip()) else "env"
    return {
        "workspace_id": org_row_id,
        "configured": _smtp_ready(org_row_id),
        "host": host or None,
        "port": port,
        "user_set": bool(user),
        "from_address": f or None,
        "use_tls": use_tls,
        "source": source,
    }


@router.get("/email_notifications/config", response_model=SmtpConfigOut)
def get_smtp_config(org_row_id: WorkspaceScopeId):
    env = env_smtp()
    t = _saved_smtp_row(org_row_id)
    if t and (t.get("host") or "").strip():
        has_pw = bool((t.get("password") or "").strip()) or bool(env["password"])
        return SmtpConfigOut(
            host=(t.get("host") or "").strip() or None,
            port=int(t.get("port") or 587),
            user=(t.get("user") or "").strip() or None,
            from_address=(t.get("from_address") or "").strip() or None,
            use_tls=bool(t.get("use_tls", True)),
            has_password=has_pw,
            source="saved",
        )
    has_pw = bool(env["password"])
    return SmtpConfigOut(
        host=env["host"] or None,
        port=int(env["port"]),
        user=env["user"] or None,
        from_address=env["from_address"] or None,
        use_tls=bool(env["use_tls"]),
        has_password=has_pw,
        source="env",
    )


@router.put("/email_notifications/config")
def put_smtp_config(org_row_id: WorkspaceScopeId, payload: SmtpConfigIn):
    tid = _sanitize_org_row_id(org_row_id)
    all_data = dict(load_smtp_settings_store())
    prev = all_data.get(tid, {}) if isinstance(all_data.get(tid), dict) else {}

    new_pw: str | None
    if payload.password is not None:
        new_pw = payload.password
    else:
        new_pw = (prev.get("password") or "").strip() or None
        if not new_pw:
            new_pw = env_smtp()["password"]
    if not new_pw:
        raise HTTPException(
            status_code=400,
            detail="SMTP password is required: enter it in the form, or set FF_SMTP_PASSWORD on the server.",
        )

    row = {
        "host": payload.host.strip(),
        "port": payload.port,
        "user": payload.user.strip(),
        "from_address": payload.from_address.strip(),
        "use_tls": payload.use_tls,
        "password": new_pw,
    }

    all_data[tid] = row
    save_smtp_settings_store(all_data)
    return {
        "ok": True,
        "message": "SMTP settings saved on the API server for this workspace.",
    }


@router.delete("/email_notifications/config")
def delete_smtp_config(org_row_id: WorkspaceScopeId):
    """Remove stored app SMTP settings; environment variables apply when set."""
    tid = _sanitize_org_row_id(org_row_id)
    all_data = dict(load_smtp_settings_store())
    if tid in all_data:
        del all_data[tid]
        save_smtp_settings_store(all_data)
    return {"ok": True, "message": "Saved SMTP settings cleared. Environment defaults apply if set."}


@router.post("/email_notifications/test")
def send_test_email(org_row_id: WorkspaceScopeId, payload: EmailNotificationTestBody):
    if not _smtp_ready(org_row_id):
        raise HTTPException(
            status_code=503,
            detail="SMTP is not configured. Use the form to save your outbound mail settings, "
            "or set FF_SMTP_* in the API environment.",
        )

    text = (payload.text or "").strip() or (
        "This is a test from Piecemint. If you received this, SMTP is set up."
    )
    subj = (payload.subject or "Piecemint - test email").strip()

    try:
        send_plain_email(org_row_id, [str(payload.to)], subj, text)
    except SmtpSendError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        log.exception("email_notifications test send failed")
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected error while sending mail: {e}",
        ) from e

    return {
        "ok": True,
        "to": str(payload.to),
        "message": "Message accepted by the mail server.",
    }
