from fastapi import APIRouter

from api.deps import DbSession, WorkspaceScopeId
from api.workspace_data import get_workspace_data

router = APIRouter()


@router.get("/tax_calculator/estimate")
def estimate_tax(db: DbSession, org_row_id: WorkspaceScopeId, tax_rate: float = 0.20):
    data = get_workspace_data(db, org_row_id)
    total_income = sum(t["amount"] for t in data["transactions"] if t["type"] == "income")
    tax_reserve = total_income * tax_rate
    return {
        "total_income": total_income,
        "tax_rate": tax_rate,
        "tax_reserve": tax_reserve,
    }
