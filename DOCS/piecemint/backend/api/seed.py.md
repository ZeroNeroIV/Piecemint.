# Initial data seed (idempotent)

**Source file:** `piecemint/backend/api/seed.py`

## Overview

- **`ensure_seed_data(db)`** runs only when the `tenants` table is empty.

- Inserts one org row and sample clients, suppliers, transactions, and stockholders for the default demo workspace.

- Called from **`api/main.py`** lifespan at startup so demos work without manual SQL.
