from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api.workspace_scope import PRIMARY_WORKSPACE_ROW_ID


def get_workspace_scope_id() -> str:
    """Piecemint is single-workspace (self-hosted); scope to the primary org row FK."""
    return PRIMARY_WORKSPACE_ROW_ID


WorkspaceScopeId = Annotated[str, Depends(get_workspace_scope_id)]
DbSession = Annotated[Session, Depends(get_db)]
