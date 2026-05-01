import io
import mimetypes
import os
import zipfile
from pathlib import Path
from typing import Any, List

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from plugin_icon import resolve_plugin_icon_path


app = FastAPI(title="MarketPlace API")

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # Wildcard origins are incompatible with credentialed browser requests; public catalog API
    # does not need cookies.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Plugin(BaseModel):
    id: str
    name: str
    description: str
    price: str
    is_free: bool
    has_icon: bool


# marketplace/backend/main.py → repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PIECEMINT_BACKEND = REPO_ROOT / "piecemint" / "backend"


def _should_skip_zip_path(path: Path) -> bool:
    parts = set(path.parts)
    if "__pycache__" in parts:
        return True
    if path.name.startswith(".") and path.name not in (".gitignore",):
        return True
    suffix = path.suffix.lower()
    return suffix in (".pyc", ".pyo")


def _plugin_source_dir(plugin_id: str) -> Path | None:
    for sub in ("plugins", "disabled_plugins"):
        d = PIECEMINT_BACKEND / sub / plugin_id
        if d.is_dir() and (d / "logic.py").exists() and (d / "manifest.yaml").exists():
            return d
    return None


def _manifest_marketplace(meta: dict[str, Any] | None) -> tuple[str, bool]:
    """Optional manifest section for display-only pricing."""
    if not meta:
        return "Free", True
    block = meta.get("marketplace")
    if not isinstance(block, dict):
        return "Free", True
    price = block.get("price")
    if not isinstance(price, str) or not price.strip():
        price = "Free"
    else:
        price = price.strip()
    is_free = bool(block.get("is_free", True))
    return price, is_free


def discover_piecemint_plugins() -> List[Plugin]:
    """Build the catalog from the same tree the main Piecemint app loads (enabled + disabled)."""
    found: dict[str, Plugin] = {}
    for sub in ("plugins", "disabled_plugins"):
        root = PIECEMINT_BACKEND / sub
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            pid = child.name
            if pid in found:
                continue
            manifest_path = child / "manifest.yaml"
            logic_path = child / "logic.py"
            if not manifest_path.is_file() or not logic_path.is_file():
                continue
            with open(manifest_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            name = str(raw.get("name") or pid).strip() or pid
            description = str(raw.get("description") or "").strip() or name
            price, is_free = _manifest_marketplace(raw if isinstance(raw, dict) else None)
            meta = raw if isinstance(raw, dict) else None
            icon_abs = resolve_plugin_icon_path(str(child), meta)
            found[pid] = Plugin(
                id=pid,
                name=name,
                description=description,
                price=price,
                is_free=is_free,
                has_icon=icon_abs is not None,
            )
    return sorted(found.values(), key=lambda p: p.name.lower())


# Populated at import; restart the API after adding plugin folders.
PLUGINS: List[Plugin] = discover_piecemint_plugins()


@app.get("/api/health")
def health():
    """Liveness probe (Render, docker compose, debugging)."""
    spa_raw = os.environ.get("MARKETPLACE_STATIC_DIR", "").strip()
    spa_ok = bool(spa_raw) and os.path.isdir(spa_raw)
    pm_ok = PIECEMINT_BACKEND.is_dir()
    plugins_ok = (PIECEMINT_BACKEND / "plugins").is_dir()
    # Render only needs 2xx — keep `ok: true` whenever the process is up.
    warnings: list[str] = []
    if not pm_ok:
        warnings.append("piecemint backend path missing — clone full monorepo for catalog")
    elif not plugins_ok:
        warnings.append("piecemint backend/plugins missing — image build may be incomplete")
    elif not spa_ok and spa_raw:
        warnings.append("MARKETPLACE_STATIC_DIR set but directory missing")
    return {
        "ok": True,
        "status": "ok" if not warnings else "degraded",
        "catalog_plugins": len(PLUGINS),
        "repo_root_piecemint_expected": str(PIECEMINT_BACKEND),
        "piecemint_backend_exists": pm_ok,
        "piecemint_plugins_dir_exists": plugins_ok,
        "spa_mount_configured": bool(spa_raw),
        "spa_static_dir_present": spa_ok,
        "warnings": warnings,
    }


@app.get("/api/plugins/{plugin_id}/download")
def download_plugin_bundle(plugin_id: str):
    """Zip bundle for import via Piecemint → Add plugin → Upload .zip (one top-level folder)."""
    plugin = next((p for p in PLUGINS if p.id == plugin_id), None)
    if not plugin:
        raise HTTPException(status_code=404, detail="Unknown plugin id.")

    src = _plugin_source_dir(plugin_id)
    if src is None:
        raise HTTPException(
            status_code=404,
            detail="Plugin source is missing from the repository (expected under piecemint/backend/plugins or disabled_plugins).",
        )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(src.rglob("*")):
            if not f.is_file():
                continue
            try:
                rel = f.relative_to(src)
            except ValueError:
                continue
            if _should_skip_zip_path(rel):
                continue
            arc = f"{plugin_id}/{rel.as_posix()}"
            zf.write(f, arc)

    data = buf.getvalue()
    if not data:
        raise HTTPException(status_code=500, detail="Bundle is empty.")
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{plugin_id}.ffplugin.zip"'},
    )


@app.get("/api/plugins/{plugin_id}/icon")
def plugin_icon(plugin_id: str):
    """Same image the main Piecemint app serves under /api/plugin-assets/{id}."""
    if (
        not plugin_id
        or "/" in plugin_id
        or "\\" in plugin_id
        or plugin_id in (".", "..")
        or plugin_id != Path(plugin_id).name
    ):
        raise HTTPException(status_code=404, detail="Unknown plugin id.")
    src = _plugin_source_dir(plugin_id)
    if src is None:
        raise HTTPException(status_code=404, detail="Unknown plugin id.")
    with open(src / "manifest.yaml", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    meta = raw if isinstance(raw, dict) else None
    path = resolve_plugin_icon_path(str(src), meta)
    if not path:
        raise HTTPException(status_code=404, detail="This plugin has no manifest icon.")
    media_type, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=media_type or "application/octet-stream")


@app.get("/api/plugins", response_model=List[Plugin])
def get_plugins():
    return PLUGINS


def _spa_static_dir() -> str | None:
    raw = os.environ.get("MARKETPLACE_STATIC_DIR", "").strip()
    if not raw or not os.path.isdir(raw):
        return None
    return raw


SPA_STATIC_DIR = _spa_static_dir()

# Production: serve the Vite build without `app.mount("/", StaticFiles)`.
# A root StaticFiles Mount can interfere with `/api/*` routing on some ASGI stacks
# behind reverse proxies — register explicit SPA routes AFTER all API routes above.
if SPA_STATIC_DIR is not None:
    _SPA_ROOT = Path(SPA_STATIC_DIR).resolve()
    _SPA_INDEX = _SPA_ROOT / "index.html"

    def _spa_file_for_url_path(url_path: str) -> Path | None:
        rel = url_path.strip().strip("/").replace("\\", "/")
        if not rel:
            return None
        parts = rel.split("/")
        if ".." in parts:
            return None
        cand = (_SPA_ROOT / rel).resolve()
        try:
            cand.relative_to(_SPA_ROOT)
        except ValueError:
            return None
        return cand if cand.is_file() else None

    if _SPA_INDEX.is_file():

        @app.get("/")
        def _spa_index():
            return FileResponse(_SPA_INDEX)

        @app.get("/{full_path:path}")
        def _spa_or_asset(full_path: str):
            if full_path == "api" or full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="Not Found")
            hit = _spa_file_for_url_path(full_path)
            if hit is not None:
                return FileResponse(hit)
            return FileResponse(_SPA_INDEX)
