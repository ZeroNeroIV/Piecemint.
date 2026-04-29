import os
import yaml
import importlib.util
from pathlib import Path

from plugin_icon import plugin_dict_with_icon, resolve_plugin_icon_path


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
