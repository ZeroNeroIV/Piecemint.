"""Same rules as piecemint/backend/plugin_icon.py — optional manifest `icon` (safe local files)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

ALLOWED_ICON_SUFFIXES = frozenset({".svg", ".png", ".webp", ".jpeg", ".jpg", ".gif", ".ico"})


def normalize_icon_relpath(raw: Any) -> str | None:
    if raw is None or not isinstance(raw, str):
        return None
    p = raw.strip().replace("\\", "/").lstrip("/")
    if not p or ".." in Path(p).parts:
        return None
    suffix = Path(p).suffix.lower()
    if suffix not in ALLOWED_ICON_SUFFIXES:
        return None
    return p


def resolve_plugin_icon_path(plugin_root: str, manifest: dict[str, Any] | None) -> str | None:
    if not manifest:
        return None
    rel = normalize_icon_relpath(manifest.get("icon"))
    if not rel:
        return None
    root = Path(plugin_root).resolve()
    full = (root / rel).resolve()
    try:
        full.relative_to(root)
    except ValueError:
        return None
    if full.is_file():
        return str(full)
    return None
