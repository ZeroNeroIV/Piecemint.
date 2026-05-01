from typing import List

from fastapi import APIRouter, HTTPException

from api import db_models
from api.deps import DbSession, WorkspaceScopeId
from api.models import (
    Client,
    ClientCreate,
    Stockholder,
    StockholderCreate,
    Supplier,
    SupplierCreate,
    Transaction,
    TransactionCreate,
    WorkspaceSummary,
)

router = APIRouter(prefix="/api/core")


def _client_out(c: db_models.Client) -> Client:
    return Client(
        id=c.id,
        name=c.name,
        email=c.email,
        total_billed=c.total_billed,
    )


def _supplier_out(s: db_models.Supplier) -> Supplier:
    return Supplier(
        id=s.id,
        name=s.name,
        email=s.email,
        total_billed=s.total_billed,
    )


def _tx_out(t: db_models.Transaction) -> Transaction:
    return Transaction(
        id=t.id,
        amount=t.amount,
        date=t.date,
        type=t.type,
        category=t.category,
        notes=t.notes or "",
        is_recurring=t.is_recurring,
        last_activity=t.last_activity,
    )


def _sh_out(s: db_models.Stockholder) -> Stockholder:
    pct = float(s.share_percent) if s.share_percent is not None else None
    return Stockholder(
        id=s.id,
        name=s.name,
        email=s.email,
        share_percent=pct,
        notes=s.notes or "",
    )


@router.get("/workspace", response_model=WorkspaceSummary)
def get_workspace(db: DbSession) -> WorkspaceSummary:
    """Single-workspace deployments: summary of the primary org row (FK for finance data)."""
    row = db.query(db_models.Tenant).order_by(db_models.Tenant.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not initialized (no org row).")
    return WorkspaceSummary(id=row.id, name=row.name)


# --- CRM: clients (FK `tenant_id`; API scopes to PRIMARY_WORKSPACE_ROW_ID) ---


@router.get("/clients", response_model=List[Client])
def get_clients(db: DbSession, org_row_id: WorkspaceScopeId) -> List[Client]:
    rows = (
        db.query(db_models.Client)
        .filter(db_models.Client.tenant_id == org_row_id)
        .order_by(db_models.Client.name)
        .all()
    )
    return [_client_out(c) for c in rows]


@router.post("/clients", response_model=Client)
def create_client(db: DbSession, org_row_id: WorkspaceScopeId, body: ClientCreate) -> Client:
    c = db_models.Client(
        tenant_id=org_row_id,
        name=body.name,
        email=body.email,
        total_billed=body.total_billed,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _client_out(c)


@router.delete("/clients/{client_id}", status_code=204)
def delete_client(db: DbSession, org_row_id: WorkspaceScopeId, client_id: str) -> None:
    c = (
        db.query(db_models.Client)
        .filter(db_models.Client.id == client_id, db_models.Client.tenant_id == org_row_id)
        .first()
    )
    if not c:
        raise HTTPException(404, "Client not found in this workspace")
    db.delete(c)
    db.commit()


# --- Suppliers ---


@router.get("/suppliers", response_model=List[Supplier])
def get_suppliers(db: DbSession, org_row_id: WorkspaceScopeId) -> List[Supplier]:
    rows = (
        db.query(db_models.Supplier)
        .filter(db_models.Supplier.tenant_id == org_row_id)
        .order_by(db_models.Supplier.name)
        .all()
    )
    return [_supplier_out(s) for s in rows]


@router.post("/suppliers", response_model=Supplier)
def create_supplier(db: DbSession, org_row_id: WorkspaceScopeId, body: SupplierCreate) -> Supplier:
    s = db_models.Supplier(
        tenant_id=org_row_id,
        name=body.name,
        email=body.email,
        total_billed=body.total_billed,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _supplier_out(s)


# --- Transactions ---


@router.get("/transactions", response_model=List[Transaction])
def get_transactions(db: DbSession, org_row_id: WorkspaceScopeId) -> List[Transaction]:
    rows = (
        db.query(db_models.Transaction)
        .filter(db_models.Transaction.tenant_id == org_row_id)
        .order_by(db_models.Transaction.date)
        .all()
    )
    return [_tx_out(t) for t in rows]


@router.post("/transactions", response_model=Transaction)
def create_transaction(
    db: DbSession, org_row_id: WorkspaceScopeId, body: TransactionCreate
) -> Transaction:
    last = body.last_activity or body.date
    t = db_models.Transaction(
        tenant_id=org_row_id,
        amount=body.amount,
        date=body.date,
        type=body.type,
        category=body.category,
        notes=body.notes or "",
        is_recurring=body.is_recurring,
        last_activity=last,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _tx_out(t)


# --- Stockholders (scoped by same org FK as clients) ---


@router.get("/stockholders", response_model=List[Stockholder])
def get_stockholders(db: DbSession, org_row_id: WorkspaceScopeId) -> List[Stockholder]:
    rows = (
        db.query(db_models.Stockholder)
        .filter(db_models.Stockholder.tenant_id == org_row_id)
        .order_by(db_models.Stockholder.name)
        .all()
    )
    return [_sh_out(s) for s in rows]


@router.post("/stockholders", response_model=Stockholder)
def create_stockholder(
    db: DbSession, org_row_id: WorkspaceScopeId, body: StockholderCreate
) -> Stockholder:
    s = db_models.Stockholder(
        tenant_id=org_row_id,
        name=body.name,
        email=body.email,
        share_percent=body.share_percent,
        notes=body.notes,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _sh_out(s)


@router.delete("/stockholders/{stockholder_id}", status_code=204)
def delete_stockholder(
    db: DbSession, org_row_id: WorkspaceScopeId, stockholder_id: str
) -> None:
    s = (
        db.query(db_models.Stockholder)
        .filter(
            db_models.Stockholder.id == stockholder_id,
            db_models.Stockholder.tenant_id == org_row_id,
        )
        .first()
    )
    if not s:
        raise HTTPException(404, "Stockholder not found in this workspace")
    db.delete(s)
    db.commit()


@router.put("/stockholders/{stockholder_id}", response_model=Stockholder)
def update_stockholder(
    db: DbSession, org_row_id: WorkspaceScopeId, stockholder_id: str, body: StockholderCreate
) -> Stockholder:
    s = (
        db.query(db_models.Stockholder)
        .filter(
            db_models.Stockholder.id == stockholder_id,
            db_models.Stockholder.tenant_id == org_row_id,
        )
        .first()
    )
    if not s:
        raise HTTPException(404, "Stockholder not found in this workspace")
    s.name = body.name
    s.email = body.email
    s.share_percent = body.share_percent
    s.notes = body.notes
    db.commit()
    db.refresh(s)
    return _sh_out(s)
