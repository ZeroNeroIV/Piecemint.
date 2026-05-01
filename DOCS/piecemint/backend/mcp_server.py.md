# MCP (Model Context Protocol) stdio server

**Source file:** `piecemint/backend/mcp_server.py`

## Overview

- Uses **`mcp.server.fastmcp.FastMCP`** with **`mcp.run()`** (stdio transport) for Cursor/OpenCode/Claude Desktop style hosts.

- Shares the same SQLite file as the FastAPI app via **`api.database`** (run from **`piecemint/backend`** so paths match).

- Core tools (workspace via **`primary_org_fk`**): **`get_clients`**, **`get_stockholders`**, **`add_stockholder`**, **`list_transactions`**, **`email_and_invoice_capabilities`**, **`send_email`**, **`send_invoice_email`** (invoice helpers load only if **`invoice_gen`** is present).

- **`send_invoice_email`** reads ORM **`Client`** fields inside the DB session before calling **`render_invoice`** (avoids **`DetachedInstanceError`** after **`session_scope()`** exits).

- **`PluginManager().apply_mcp_extras(mcp)`** runs after builtins; optional per-plugin **`mcp_extras.py`** implementations populate **`plugin_mcp_extras_loaded`** in **`email_and_invoice_capabilities`**.

- Entry: `pipenv run python mcp_server.py` from `piecemint/backend`.
