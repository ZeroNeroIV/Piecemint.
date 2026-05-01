# FastAPI dependencies: DB session and workspace scope

**Source file:** `piecemint/backend/api/deps.py`

## Overview

- **`get_workspace_scope_id`**: returns the primary org FK (`PRIMARY_WORKSPACE_ROW_ID`) for this deployment.

- **`WorkspaceScopeId`**: `Annotated[str, Depends(get_workspace_scope_id)]` for concise route parameters.

- **`DbSession`**: `Annotated[Session, Depends(get_db)]` for SQLAlchemy sessions per request.
