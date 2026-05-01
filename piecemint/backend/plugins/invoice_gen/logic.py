import sys
from pathlib import Path

_plug = str(Path(__file__).resolve().parent)
if _plug not in sys.path:
    sys.path.insert(0, _plug)

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from api import db_models
from api.deps import DbSession, WorkspaceScopeId
from api.smtp_outbound import SmtpSendError, send_email_with_attachments, smtp_is_configured

from builders import render_invoice
from schemas import InvoiceExportConfig

router = APIRouter()


def _get_client(db: Session, client_id: str, org_row_id: str) -> db_models.Client | None:
    return (
        db.query(db_models.Client)
        .filter(
            db_models.Client.id == client_id,
            db_models.Client.tenant_id == org_row_id,
        )
        .first()
    )


def _invoice_response(c: db_models.Client, cfg: InvoiceExportConfig) -> Response:
    content, media_type, ext = render_invoice(
        c.name,
        c.email,
        c.id,
        float(c.total_billed),
        cfg,
    )
    safe_id = "".join(ch for ch in c.id if ch.isalnum() or ch in "-_")[:40] or "client"
    filename = f"invoice_{safe_id}{ext}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/invoice_gen/generate/{client_id}")
def generate_invoice_get(client_id: str, db: DbSession, org_row_id: WorkspaceScopeId):
    """Legacy GET: PDF with default styling (same as empty config)."""
    c = _get_client(db, client_id, org_row_id)
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    return _invoice_response(c, InvoiceExportConfig())


@router.post("/invoice_gen/generate/{client_id}")
def generate_invoice_post(
    client_id: str,
    db: DbSession,
    org_row_id: WorkspaceScopeId,
    config: InvoiceExportConfig = Body(...),
):
    c = _get_client(db, client_id, org_row_id)
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    return _invoice_response(c, config)


class InvoiceEmailRequest(BaseModel):
    config: InvoiceExportConfig
    to: EmailStr | None = None
    subject: str | None = Field(None, max_length=998)
    body: str | None = Field(None, max_length=50_000)


@router.post("/invoice_gen/email/{client_id}")
def email_invoice_post(
    client_id: str,
    db: DbSession,
    org_row_id: WorkspaceScopeId,
    req: InvoiceEmailRequest,
):
    """Send the rendered invoice as an attachment via SMTP (same settings as Email notifications)."""
    c = _get_client(db, client_id, org_row_id)
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")

    to_addr = (str(req.to).strip() if req.to else None) or ((c.email or "").strip() or None)
    if not to_addr:
        raise HTTPException(
            status_code=400,
            detail="No recipient email: add an email on the client or pass `to` in the request body.",
        )

    if not smtp_is_configured(org_row_id):
        raise HTTPException(
            status_code=503,
            detail="SMTP is not configured. Open the Email notifications plugin and save mail settings, "
            "or set FF_SMTP_* on the server.",
        )

    content, media_type, ext = render_invoice(
        c.name,
        c.email,
        c.id,
        float(c.total_billed),
        req.config,
    )

    doc = req.config.invoice_document
    inv = (doc.invoice_number or "").strip() if doc else ""
    default_subj = f"Invoice {inv}" if inv else f"Invoice — {c.name}"
    subj = (req.subject or "").strip() or default_subj

    default_body = (
        f"Hello,\n\nPlease find your invoice attached.\n\n"
        f"Thank you,\n{c.name} (via Piecemint)\n"
    )
    text_body = (req.body or "").strip() or default_body

    safe_id = "".join(ch for ch in c.id if ch.isalnum() or ch in "-_")[:40] or "client"
    filename = f"invoice_{safe_id}{ext}"

    try:
        send_email_with_attachments(
            org_row_id,
            [to_addr],
            subj,
            text_body,
            [(filename, content, media_type)],
        )
    except SmtpSendError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return {"ok": True, "to": to_addr, "subject": subj, "filename": filename}
