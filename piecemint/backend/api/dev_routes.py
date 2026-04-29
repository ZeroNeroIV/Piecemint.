"""
Local / self-hosted utilities: install a plugin by writing files under backend/plugins/.

Set FF_DISABLE_PLUGIN_UPLOAD=1 to block writes (recommended in production).
"""

from __future__ import annotations

import io
import os
import re
import shutil
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/dev", tags=["dev"])

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = BACKEND_ROOT / "plugins"

PLUGIN_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,48}$")


class PluginInstallBody(BaseModel):
    plugin_id: str = Field(..., min_length=2, max_length=50)
    logic_py: str = Field(..., min_length=20)
    manifest_yaml: str | None = None
    overwrite: bool = False

    @field_validator("plugin_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        t = v.strip()
        if not PLUGIN_ID_RE.fullmatch(t):
            raise ValueError(
                "plugin_id must start with a letter and contain only lowercase letters, digits, and underscores."
            )
        return t


def _upload_disabled() -> bool:
    return os.environ.get("FF_DISABLE_PLUGIN_UPLOAD", "").lower() in ("1", "true", "yes")


def _default_manifest(plugin_id: str) -> str:
    title = plugin_id.replace("_", " ").title()
    return (
        f'name: "{title}"\n'
        f'description: "Custom plugin {plugin_id}."\n'
        'version: "1.0.0"\n'
    )


def _protected_plugin_ids() -> set[str]:
    raw = os.environ.get("FF_PROTECTED_PLUGINS", "invoice_gen,expense_categorizer,tax_calculator")
    return {p.strip() for p in raw.split(",") if p.strip()}


@router.post("/plugins/install_zip")
async def install_plugin_zip(
    file: UploadFile = File(..., description=".zip from the public marketplace (one top-level folder)"),
    overwrite: bool = Form(False),
):
    """
    Extract a plugin `.zip` into `plugins/<id>/`. Zip must contain exactly one top-level directory matching
    `plugin_id` with `logic.py` and `manifest.yaml` inside. Restart the API after install.
    """
    if _upload_disabled():
        raise HTTPException(
            status_code=403,
            detail="Plugin upload is disabled (set FF_DISABLE_PLUGIN_UPLOAD=0 on the server to allow).",
        )

    raw = await file.read()
    if len(raw) > 5_000_000:
        raise HTTPException(status_code=400, detail="Zip file too large (max 5 MB).")

    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as e:
        raise HTTPException(status_code=400, detail="Invalid zip file.") from e

    with zf:
        members = [m for m in zf.infolist() if not m.is_dir()]
        if not members:
            raise HTTPException(status_code=400, detail="Zip has no files.")

        tops: set[str] = set()
        for m in members:
            name = m.filename.replace("\\", "/").strip("/")
            if not name or ".." in name.split("/"):
                raise HTTPException(status_code=400, detail="Invalid path inside zip.")
            tops.add(name.split("/")[0])
        if len(tops) != 1:
            raise HTTPException(
                status_code=400,
                detail="Zip must contain exactly one top-level folder (the plugin id), e.g. my_plugin/logic.py.",
            )
        plugin_id = tops.pop()
        if not PLUGIN_ID_RE.fullmatch(plugin_id):
            raise HTTPException(
                status_code=400,
                detail=f"Top-level folder name is not a valid plugin id: {plugin_id!r}.",
            )

        dest = PLUGINS_DIR / plugin_id
        if dest.exists() and not overwrite:
            raise HTTPException(
                status_code=409,
                detail=f"Plugin folder already exists: {plugin_id}. Pass overwrite=true to replace.",
            )
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)

        for m in members:
            name = m.filename.replace("\\", "/").strip("/")
            if not name.startswith(f"{plugin_id}/"):
                raise HTTPException(status_code=400, detail="Unexpected path in zip (wrong prefix).")
            rel = name[len(plugin_id) + 1 :]
            if not rel or ".." in rel.split("/"):
                raise HTTPException(status_code=400, detail="Bad relative path in zip.")
            out_path = (dest / rel).resolve()
            try:
                out_path.relative_to(dest.resolve())
            except ValueError as e:
                raise HTTPException(status_code=400, detail="Path escapes plugin folder.") from e
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(m) as src, open(out_path, "wb") as dst:
                dst.write(src.read())

    code = (dest / "logic.py").read_text(encoding="utf-8")
    if "router" not in code or "APIRouter" not in code:
        shutil.rmtree(dest, ignore_errors=True)
        raise HTTPException(
            status_code=400,
            detail="logic.py must define a FastAPI APIRouter (e.g. router = APIRouter()).",
        )
    manifest = dest / "manifest.yaml"
    if not manifest.exists():
        shutil.rmtree(dest, ignore_errors=True)
        raise HTTPException(status_code=400, detail="manifest.yaml missing after extracting zip.")

    return {
        "ok": True,
        "plugin_id": plugin_id,
        "path": str(dest.relative_to(BACKEND_ROOT)),
        "message": "Plugin extracted. Restart the API server, then refresh the plugin list in the app.",
    }


@router.delete("/plugins/{plugin_id}")
def delete_plugin(plugin_id: str):
    """Remove `plugins/<plugin_id>/` from disk. Restart the API. Bundled ids can be protected via FF_PROTECTED_PLUGINS."""
    if _upload_disabled():
        raise HTTPException(
            status_code=403,
            detail="Plugin maintenance is disabled (FF_DISABLE_PLUGIN_UPLOAD=1).",
        )
    t = plugin_id.strip()
    if not PLUGIN_ID_RE.fullmatch(t):
        raise HTTPException(status_code=400, detail="Invalid plugin id.")
    if t in _protected_plugin_ids():
        raise HTTPException(
            status_code=403,
            detail=f"Plugin {t!r} is protected (set FF_PROTECTED_PLUGINS to change).",
        )
    dest = PLUGINS_DIR / t
    if not dest.is_dir():
        raise HTTPException(status_code=404, detail=f"Plugin not installed: {t}")
    try:
        shutil.rmtree(dest)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {e}") from e
    return {
        "ok": True,
        "plugin_id": t,
        "message": "Plugin removed from disk. Restart the API server to unload routes.",
    }


@router.post("/plugins/install")
def install_plugin(body: PluginInstallBody):
    """
    Write `logic.py` (and optional `manifest.yaml`) into `plugins/<plugin_id>/`.

    Requires a `router = APIRouter()` in logic_py. Restart the API process to load the new plugin.
    """
    if _upload_disabled():
        raise HTTPException(
            status_code=403,
            detail="Plugin upload is disabled (set FF_DISABLE_PLUGIN_UPLOAD=0 on the server to allow).",
        )

    code = body.logic_py
    if "router" not in code or "APIRouter" not in code:
        raise HTTPException(
            status_code=400,
            detail="logic.py must define a FastAPI APIRouter (e.g. router = APIRouter()).",
        )

    dest = PLUGINS_DIR / body.plugin_id
    if dest.exists() and not body.overwrite:
        raise HTTPException(
            status_code=409,
            detail=f"Plugin folder already exists: {body.plugin_id}. Pass overwrite: true to replace.",
        )

    manifest = body.manifest_yaml.strip() if body.manifest_yaml else _default_manifest(body.plugin_id)
    if "name:" not in manifest:
        raise HTTPException(status_code=400, detail="manifest.yaml must contain a name: field.")

    try:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "logic.py").write_text(code, encoding="utf-8")
        (dest / "manifest.yaml").write_text(manifest if manifest.endswith("\n") else manifest + "\n", encoding="utf-8")
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to write files: {e}") from e

    return {
        "ok": True,
        "plugin_id": body.plugin_id,
        "path": str(dest.relative_to(BACKEND_ROOT)),
        "message": "Files written. Restart the API server, then refresh the plugin list in the app.",
    }
