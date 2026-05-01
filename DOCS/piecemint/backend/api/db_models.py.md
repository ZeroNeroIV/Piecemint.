# ORM models: org row + finance tables

**Source file:** `piecemint/backend/api/db_models.py`

## Overview

- **`Tenant`**: org/workspace master row (`tenants.id`). Child tables use FK column `tenant_id` (name unchanged for DB compatibility).

- **`Client`**, **`Supplier`**, **`Transaction`**, **`Stockholder`**: scoped by that FK with business fields matching the API/seed data.

- **`Transaction`**: stores `date` / `last_activity` as strings (ISO dates) for simple JSON alignment with the frontend.

- Uses SQLAlchemy 2.0 `Mapped[]` / `mapped_column` style.
