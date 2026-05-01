# Plugin: PDF invoice generation

**Source file:** `piecemint/backend/plugins/invoice_gen/logic.py`

## Overview

- **`GET /invoice_gen/generate/{client_id}`** loads a **`Client`** for the scoped workspace, returns **`application/pdf`** (ReportLab canvas).

- 404 if the client id does not exist in this workspace.
