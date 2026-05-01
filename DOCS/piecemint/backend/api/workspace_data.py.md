# Read model for plugins (dict compatibility)

**Source file:** `piecemint/backend/api/workspace_data.py`

## Overview

- **`ensure_org_row`**: creates a **`Tenant`** ORM row if an unknown org id is used.

- **`get_workspace_data(db, org_row_id)`** returns `clients`, `suppliers`, `transactions` as plain dict lists (legacy mock `DB` shape).

- **`primary_org_fk`** supports MCP callers that resolve the first org row.

- Imported by plugin `logic.py` files for tax, expenses, and AI without duplicating query logic.
