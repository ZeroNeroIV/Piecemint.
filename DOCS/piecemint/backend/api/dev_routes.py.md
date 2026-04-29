# Development-only routes (plugin install)

**Source file:** `piecemint/backend/api/dev_routes.py`

## Overview

- **`/api/dev/plugins/install`** and **`install_zip`**: write plugin folders under **`plugins/<id>/`** from pasted Python or a marketplace-style zip.

- Guarded by env (e.g. upload disable flags); restart API to load new plugin routers.
