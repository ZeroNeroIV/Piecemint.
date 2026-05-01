from pydantic import BaseModel, Field


class Client(BaseModel):
    id: str
    name: str
    email: str
    total_billed: float


class ClientCreate(BaseModel):
    name: str
    email: str = ""
    total_billed: float = 0.0


class Supplier(BaseModel):
    id: str
    name: str
    email: str
    total_billed: float


class SupplierCreate(BaseModel):
    name: str
    email: str = ""
    total_billed: float = 0.0


class Transaction(BaseModel):
    id: str
    amount: float
    date: str
    type: str  # income | expense
    category: str
    notes: str = ""
    is_recurring: bool
    last_activity: str


class TransactionCreate(BaseModel):
    amount: float
    date: str
    type: str
    category: str = ""
    notes: str = ""
    is_recurring: bool = False
    last_activity: str | None = None


class Stockholder(BaseModel):
    id: str
    name: str
    email: str = ""
    share_percent: float | None = None
    notes: str = ""


class StockholderCreate(BaseModel):
    name: str
    email: str = ""
    share_percent: float | None = None
    notes: str = ""


class WorkspaceSummary(BaseModel):
    """Primary org row for this deployment (SQLite/Postgres `tenants.id`)."""

    id: str
    name: str
