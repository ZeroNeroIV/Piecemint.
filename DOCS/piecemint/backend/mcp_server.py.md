# MCP (Model Context Protocol) stdio server

**Source file:** `piecemint/backend/mcp_server.py`

## Overview

- Uses **`mcp.server.fastmcp.FastMCP`** with **`mcp.run()`** (stdio transport) for Cursor/Claude Desktop style hosts.

- Shares the same SQLite file as the FastAPI app via **`api.database`**.

- Tools scope to **`primary_org_fk`**: **`get_clients`**, **`get_stockholders`**, **`add_stockholder`**, **`list_transactions`**, **`send_email`**, **`send_invoice_email`**.

- Entry: `pipenv run python mcp_server.py` from `piecemint/backend`.
