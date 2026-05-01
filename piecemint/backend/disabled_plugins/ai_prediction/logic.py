import calendar
from datetime import datetime

import pandas as pd
from fastapi import APIRouter

from api.deps import DbSession, WorkspaceScopeId
from api.workspace_data import get_workspace_data

router = APIRouter()


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day)


@router.get("/ai_prediction/forecast")
def forecast_cashflow(db: DbSession, org_row_id: WorkspaceScopeId):
    data = get_workspace_data(db, org_row_id)
    transactions = data["transactions"]
    if not transactions:
        return {"forecast": []}

    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].astype(float)

    monthly_totals = df.groupby(df["date"].dt.to_period("M"))["amount"].sum()
    if len(monthly_totals) == 0:
        return {"forecast": []}

    avg_monthly = float(monthly_totals.mean())

    last_date = df["date"].max()
    forecast = []
    for i in range(1, 4):
        next_month = add_months(last_date, i)
        forecast.append(
            {
                "month": next_month.strftime("%Y-%m"),
                "projected_cashflow": avg_monthly,
            }
        )

    return {"forecast": forecast}
