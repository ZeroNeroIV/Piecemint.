import importlib.util
import logging
import os
from pathlib import Path
from typing import Any

import yaml

from plugin_icon import plugin_dict_with_icon, resolve_plugin_icon_path

log = logging.getLogger(__name__)


class PluginManager:
    def __init__(self):
        self.plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        self.disabled_plugins_dir = os.path.join(os.path.dirname(__file__), 'disabled_plugins')
        self.installed_plugins = []
        self.routers = []

    @staticmethod
    def _read_manifest(plugin_path: str) -> dict | None:
        manifest_path = os.path.join(plugin_path, 'manifest.yaml')
        if not os.path.exists(manifest_path):
            return None
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else None

    def discover_plugins(self):
        self.installed_plugins = []
        self.routers = []

        if not os.path.exists(self.plugins_dir):
            return

        for plugin_name in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, plugin_name)
            if not os.path.isdir(plugin_path):
                continue
            manifest = self._read_manifest(plugin_path)
            if not manifest:
                continue

            logic_path = os.path.join(plugin_path, 'logic.py')
            if os.path.exists(logic_path):
                spec = importlib.util.spec_from_file_location(f"plugins.{plugin_name}.logic", logic_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, 'router'):
                    self.routers.append(module.router)

            self.installed_plugins.append(plugin_dict_with_icon(plugin_name, plugin_path, manifest))

    def register_routes(self, app):
        for router in self.routers:
            app.include_router(router, prefix="/api/plugins")

    def apply_mcp_extras(self, mcp: Any) -> list[str]:
        """
        Load optional plugins/*/mcp_extras.py for enabled plugins (same discovery rules as REST:
        directory under plugins/ with manifest.yaml).

        Each mcp_extras module may define::

            def register_mcp(mcp) -> None:
                ...  # e.g. @mcp.tool on functions or mcp.add_tool(...)

        Returns plugin IDs whose extras loaded successfully.
        """
        loaded: list[str] = []
        if not os.path.exists(self.plugins_dir):
            return loaded

        for plugin_name in sorted(os.listdir(self.plugins_dir)):
            plugin_path = os.path.join(self.plugins_dir, plugin_name)
            if not os.path.isdir(plugin_path):
                continue
            manifest = self._read_manifest(plugin_path)
            if not manifest:
                continue

            extras_path = os.path.join(plugin_path, "mcp_extras.py")
            if not os.path.isfile(extras_path):
                continue

            mod_name = f"plugins.{plugin_name}.mcp_extras"
            try:
                spec = importlib.util.spec_from_file_location(mod_name, extras_path)
                if spec is None or spec.loader is None:
                    log.warning("Could not load spec for %s", extras_path)
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception:
                log.exception("Failed to import mcp_extras for plugin %r", plugin_name)
                continue

            registrar = getattr(module, "register_mcp", None)
            if not callable(registrar):
                log.warning(
                    "Plugin %r has mcp_extras.py but no callable register_mcp(mcp)",
                    plugin_name,
                )
                continue

            try:
                registrar(mcp)
            except Exception:
                log.exception("register_mcp failed for plugin %r", plugin_name)
                continue

            loaded.append(plugin_name)

        return loaded

    def get_installed_plugins(self):
        installed = []
        if not os.path.exists(self.plugins_dir):
            return installed

        for plugin_name in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, plugin_name)
            if not os.path.isdir(plugin_path):
                continue
            manifest = self._read_manifest(plugin_path)
            if not manifest:
                continue
            installed.append(plugin_dict_with_icon(plugin_name, plugin_path, manifest))
        return installed

    def get_available_plugins(self):
        available = []
        if not os.path.exists(self.disabled_plugins_dir):
            return available

        for plugin_name in os.listdir(self.disabled_plugins_dir):
            plugin_path = os.path.join(self.disabled_plugins_dir, plugin_name)
            if not os.path.isdir(plugin_path):
                continue
            manifest = self._read_manifest(plugin_path)
            if not manifest:
                continue
            available.append(plugin_dict_with_icon(plugin_name, plugin_path, manifest))
        return available

    def get_plugin_icon_abs_path(self, plugin_id: str) -> str | None:
        if (
            not plugin_id
            or "/" in plugin_id
            or "\\" in plugin_id
            or plugin_id in (".", "..")
            or plugin_id != Path(plugin_id).name
        ):
            return None
        for parent in (self.plugins_dir, self.disabled_plugins_dir):
            plugin_path = os.path.join(parent, plugin_id)
            if not os.path.isdir(plugin_path):
                continue
            manifest = self._read_manifest(plugin_path)
            if not manifest:
                continue
            resolved = resolve_plugin_icon_path(plugin_path, manifest)
            if resolved:
                return resolved
        return None
