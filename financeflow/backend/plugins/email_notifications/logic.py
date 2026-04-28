"""
SMTP: configure per tenant via PUT /email_notifications/config (saved under plugins/.../data/)
or set FF_SMTP_* on the API host (optional fallback for password when not re-saved).
"""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from api.deps import TenantId
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

_TENANT_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def _safe_tenant(tenant_id: str) -> str:
    t = str(tenant_id).strip()
    if not _TENANT_RE.match(t):
        raise HTTPException(status_code=400, detail="Invalid tenant id.")
    return t


def _tenant_row(tenant_id: str) -> dict | None:
    tid = _safe_tenant(tenant_id)
    row = load_smtp_settings_store().get(tid)
    if not row or not isinstance(row, dict):
        return None
    return row


def _is_configured_for_tenant(tenant_id: str) -> bool:
    return smtp_is_configured(tenant_id)


class SmtpConfigOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    host: str | None = None
    port: int = 587
    user: str | None = None
    from_address: str | None = None
    use_tls: bool = True
    has_password: bool = False
    source: str  # "tenant" | "env"


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
def email_status(tenant_id: TenantId):
    host, port, user, _pw, f, use_tls = effective_smtp(tenant_id)
    t = _tenant_row(tenant_id)
    source = "tenant" if (t and (t.get("host") or "").strip()) else "env"
    return {
        "tenant_id": tenant_id,
        "configured": _is_configured_for_tenant(tenant_id),
        "host": host or None,
        "port": port,
        "user_set": bool(user),
        "from_address": f or None,
        "use_tls": use_tls,
        "source": source,
    }


@router.get("/email_notifications/config", response_model=SmtpConfigOut)
def get_smtp_config(tenant_id: TenantId):
    env = env_smtp()
    t = _tenant_row(tenant_id)
    if t and (t.get("host") or "").strip():
        has_pw = bool((t.get("password") or "").strip()) or bool(env["password"])
        return SmtpConfigOut(
            host=(t.get("host") or "").strip() or None,
            port=int(t.get("port") or 587),
            user=(t.get("user") or "").strip() or None,
            from_address=(t.get("from_address") or "").strip() or None,
            use_tls=bool(t.get("use_tls", True)),
            has_password=has_pw,
            source="tenant",
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
def put_smtp_config(tenant_id: TenantId, body: SmtpConfigIn):
    tid = _safe_tenant(tenant_id)
    all_data = dict(load_smtp_settings_store())
    prev = all_data.get(tid, {}) if isinstance(all_data.get(tid), dict) else {}

    new_pw: str | None
    if body.password is not None:
        new_pw = body.password
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
        "host": body.host.strip(),
        "port": body.port,
        "user": body.user.strip(),
        "from_address": body.from_address.strip(),
        "use_tls": body.use_tls,
        "password": new_pw,
    }

    all_data[tid] = row
    save_smtp_settings_store(all_data)
    return {
        "ok": True,
        "message": "SMTP settings saved for this tenant on the API server.",
    }


@router.delete("/email_notifications/config")
def delete_smtp_config(tenant_id: TenantId):
    """Remove stored tenant override; the API will fall back to environment variables if set."""
    tid = _safe_tenant(tenant_id)
    all_data = dict(load_smtp_settings_store())
    if tid in all_data:
        del all_data[tid]
        save_smtp_settings_store(all_data)
    return {"ok": True, "message": "Saved SMTP settings cleared. Environment defaults apply if set."}


class TestEmailBody(BaseModel):
    to: EmailStr
    subject: str | None = "Piecemint — test email"
    text: str | None = None


@router.post("/email_notifications/test")
def send_test_email(tenant_id: TenantId, body: TestEmailBody):
    if not _is_configured_for_tenant(tenant_id):
        raise HTTPException(
            status_code=503,
            detail="SMTP is not configured. Use the form to save your outbound mail settings, "
            "or set FF_SMTP_* in the API environment.",
        )

    text = (body.text or "").strip() or (
        "This is a test from Piecemint. If you received this, SMTP is set up."
    )
    subj = (body.subject or "Piecemint — test email").strip()

    try:
        send_plain_email(tenant_id, [str(body.to)], subj, text)
    except SmtpSendError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return {"ok": True, "to": body.to, "message": "Message accepted by the mail server."}
