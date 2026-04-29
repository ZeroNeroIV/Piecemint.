import io
import mimetypes
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
