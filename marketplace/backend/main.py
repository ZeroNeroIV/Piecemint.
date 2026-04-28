from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import List
from pydantic import BaseModel
import io
import zipfile
from pathlib import Path

app = FastAPI(title="MarketPlace API")

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class Plugin(BaseModel):
    id: str
    name: str
    description: str
    price: str
    is_free: bool

PLUGINS: List[Plugin] = [
    Plugin(
        id="mcp",
        name="MCP Protocol",
        description="Connect Piecemint directly to Claude for AI-powered data management.",
        price="Free",
        is_free=True
    ),
    Plugin(
        id="invoice_gen",
        name="Invoice Generator",
        description="Create, customize, and export professional invoices instantly.",
        price="Free",
        is_free=True
    ),
    Plugin(
        id="expense_categorizer",
        name="Expense Categorizer",
        description="Automatically categorize and organize your transactions.",
        price="$4.99/mo",
        is_free=False
    ),
    Plugin(
        id="tax_calculator",
        name="Tax Calculator",
        description="Estimate your tax liabilities across multiple jurisdictions.",
        price="$9.99/mo",
        is_free=False
    ),
    Plugin(
        id="small_business",
        name="Small Business Suite",
        description="Comprehensive tools tailored for small business accounting.",
        price="$14.99/mo",
        is_free=False
    ),
    Plugin(
        id="stockholders",
        name="Stockholders Management",
        description="Manage equity, dividends, and stockholder communications.",
        price="$19.99/mo",
        is_free=False
    ),
    Plugin(
        id="ai_prediction",
        name="AI Prediction",
        description="Advanced forecasting for cash flow and revenue models.",
        price="$29.99/mo",
        is_free=False
    ),
    Plugin(
        id="email_notifications",
        name="Email Notifications",
        description="Automated alerts and reports delivered straight to your inbox.",
        price="$1.99/mo",
        is_free=False
    ),
    Plugin(
        id="web_notifications",
        name="Web Notifications",
        description="Real-time push notifications for important financial events.",
        price="$1.99/mo",
        is_free=False
    )
]

# Piecemint / FinanceFlow monorepo: plugin folders live next to `marketplace/backend`.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _plugin_source_dir(plugin_id: str) -> Path | None:
    base = REPO_ROOT / "financeflow" / "backend"
    for sub in ("plugins", "disabled_plugins"):
        d = base / sub / plugin_id
        if d.is_dir() and (d / "logic.py").exists():
            return d
    return None


def _stub_files(plugin: Plugin) -> tuple[str, str]:
    logic = (
        f'"""Stub "{plugin.name}" — replace with full implementation or copy from the open-source repo."""\n'
        "from fastapi import APIRouter\n"
        f'router = APIRouter(tags=["{plugin.id}"])\n\n\n'
        f'@router.get("/{plugin.id}/health")\n'
        "def health():\n"
        f'    return {{"plugin": "{plugin.id}", "status": "ok", "note": "stub from marketplace"}}\n'
    )
    desc = plugin.description.replace('"', "'")[:240]
    manifest = (
        f'name: "{plugin.name}"\n'
        f'description: "{desc}"\n'
        'version: "1.0.0"\n'
    )
    return logic, manifest


@app.get("/api/plugins/{plugin_id}/download")
def download_plugin_bundle(plugin_id: str):
    """Zip bundle for import via Piecemint → Add plugin → Upload .zip (one top-level folder)."""
    plugin = next((p for p in PLUGINS if p.id == plugin_id), None)
    if not plugin:
        raise HTTPException(status_code=404, detail="Unknown plugin id.")

    buf = io.BytesIO()
    src = _plugin_source_dir(plugin_id)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if src is not None:
            for f in sorted(src.rglob("*")):
                if f.is_file():
                    arc = f"{plugin_id}/{f.relative_to(src).as_posix()}"
                    zf.write(f, arc)
        else:
            logic, manifest = _stub_files(plugin)
            zf.writestr(f"{plugin_id}/logic.py", logic)
            zf.writestr(f"{plugin_id}/manifest.yaml", manifest)

    data = buf.getvalue()
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{plugin_id}.ffplugin.zip"'},
    )


@app.get("/api/plugins", response_model=List[Plugin])
def get_plugins():
    return PLUGINS
