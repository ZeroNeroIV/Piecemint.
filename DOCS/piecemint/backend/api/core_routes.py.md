# Core REST API (single workspace)

**Source file:** `piecemint/backend/api/core_routes.py`

## Overview

- Router prefix: `/api/core`.

- Uses **`DbSession`** and **`WorkspaceScopeId`**: all rows are scoped to the primary org FK (self-hosted; no header pickers).

- `GET /workspace` returns the org row id and display name.

- Exposes CRUD-style routes for **clients**, **suppliers**, **transactions**, and **stockholders** against SQLAlchemy models.

- Returns Pydantic models from `api/models.py` for OpenAPI-friendly responses.
