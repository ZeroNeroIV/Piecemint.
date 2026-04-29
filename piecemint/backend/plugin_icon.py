"""Resolve optional manifest `icon` paths for plugin bundles (safe local files only)."""

from __future__ import annotations

import os
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
    """Return absolute path to icon file if manifest references a valid file under plugin_root."""
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


def plugin_dict_with_icon(
    plugin_id: str,
    plugin_path: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    icon_abs = resolve_plugin_icon_path(plugin_path, manifest)
    return {
        "id": plugin_id,
        "name": manifest.get("name", plugin_id),
        "description": manifest.get("description", ""),
        "version": manifest.get("version", "1.0.0"),
        "has_icon": icon_abs is not None,
    }
