"""Shared read model for plugins: dict shape matches the legacy mock DB layout."""

from sqlalchemy.orm import Session

from api import db_models


def ensure_org_row(db: Session, org_row_id: str) -> db_models.Tenant:
    t = db.get(db_models.Tenant, org_row_id)
    if t is None:
        t = db_models.Tenant(id=org_row_id, name=org_row_id)
        db.add(t)
        db.commit()
        db.refresh(t)
    return t


def get_workspace_data(db: Session, org_row_id: str) -> dict:
    """Return finance collections for one org row (FK on child tables stays `tenant_id`)."""
    ensure_org_row(db, org_row_id)
    clients = (
        db.query(db_models.Client)
        .filter(db_models.Client.tenant_id == org_row_id)
        .order_by(db_models.Client.name)
        .all()
    )
    suppliers = (
        db.query(db_models.Supplier)
        .filter(db_models.Supplier.tenant_id == org_row_id)
        .order_by(db_models.Supplier.name)
        .all()
    )
    transactions = (
        db.query(db_models.Transaction)
        .filter(db_models.Transaction.tenant_id == org_row_id)
        .order_by(db_models.Transaction.date)
        .all()
    )
    return {
        "clients": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "total_billed": c.total_billed,
            }
            for c in clients
        ],
        "suppliers": [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "total_billed": s.total_billed,
            }
            for s in suppliers
        ],
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "date": t.date,
                "type": t.type,
                "category": t.category,
                "notes": t.notes or "",
                "is_recurring": t.is_recurring,
                "last_activity": t.last_activity,
            }
            for t in transactions
        ],
    }


def primary_org_fk(session: Session) -> str | None:
    """First org row id (single self-hosted workspace)."""
    row = session.query(db_models.Tenant).order_by(db_models.Tenant.id).first()
    return row.id if row else None
