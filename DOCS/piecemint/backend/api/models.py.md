# Pydantic request/response models

**Source file:** `piecemint/backend/api/models.py`

## Overview

- Defines API shapes: **`Client`**, **`Supplier`**, **`Transaction`**, **`Stockholder`**, plus **`*Create`** bodies where applicable.

- **`WorkspaceSummary`**: `id` + `name` for `GET /api/core/workspace`.

- Used for response validation and OpenAPI schema in `core_routes.py`.
