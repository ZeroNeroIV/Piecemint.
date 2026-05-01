# Pydantic request/response models

**Source file:** `piecemint/backend/api/models.py`

## Overview

- Defines API shapes: **`Client`**, **`Supplier`**, **`Transaction`**, **`Stockholder`**, plus **`*Create`** bodies where applicable.

- **`WorkspaceSummary`**: `id` + `name` for `GET /api/core/workspace`.

- **`EmailNotificationTestBody`**: JSON body for **`POST /api/plugins/email_notifications/test`** (declared here so Pydantic resolves correctly when `email_notifications` is loaded as a dynamic plugin).

- Used for response validation and OpenAPI schema in `core_routes.py`.
