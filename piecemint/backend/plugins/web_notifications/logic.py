"""
No server push delivery yet: the UI uses the browser Notification API.
This router keeps workspace-scoped hooks for health checks and future VAPID/webpush integration.
"""

from __future__ import annotations

import os

from fastapi import APIRouter

from api.deps import WorkspaceScopeId

router = APIRouter()


@router.get("/web_notifications/status")
def web_notif_status(org_row_id: WorkspaceScopeId):
    vapid = os.environ.get("FF_VAPID_PUBLIC_KEY", "").strip() or None
    return {
        "workspace_id": org_row_id,
        "browser_driven": True,
        "vapid_public_key": vapid,
        "note": "Enable notifications in the plugin panel; optional FF_VAPID_* env vars for future Web Push.",
    }
