# Dynamic plugin discovery and registration

**Source file:** `piecemint/backend/plugin_manager.py`

## Overview

- Scans **`plugins/`** for subfolders with **`manifest.yaml`**.

- For each plugin with **`logic.py`**, loads the module and collects **`router`** objects; registers them on the app under prefix **`/api/plugins`**.

- **`apply_mcp_extras(mcp)`** loads optional **`mcp_extras.py`** (same manifest-gated folders) and calls **`register_mcp(mcp)`** if present; failures are logged per plugin. Used by **`mcp_server.py`** only (not FastAPI startup).

- **`get_installed_plugins()`** re-reads the filesystem for the marketplace UI; **`get_available_plugins()`** lists folders under **`disabled_plugins/`** (MCP extras are not loaded from disabled plugins).

- Note: moving a plugin only updates HTTP routes after the app process reloads; the plugin **list** can update without restart.
