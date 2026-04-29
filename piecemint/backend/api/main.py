import mimetypes
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.core_routes import router as core_router
from api.database import SessionLocal, init_db
from api.dev_routes import router as dev_router
from api.seed import ensure_seed_data
from plugin_manager import PluginManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        ensure_seed_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Piecemint API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

plugin_manager = PluginManager()
plugin_manager.discover_plugins()
plugin_manager.register_routes(app)

app.include_router(core_router)
app.include_router(dev_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Piecemint API"}


@app.get("/api/plugins")
def list_plugins():
    return {
        "installed": plugin_manager.get_installed_plugins(),
        "available": plugin_manager.get_available_plugins(),
    }


@app.get("/api/plugin-assets/{plugin_id}")
def serve_plugin_icon(plugin_id: str):
    """Serve the file named in manifest `icon:` for this plugin (enabled or disabled)."""
    path = plugin_manager.get_plugin_icon_abs_path(plugin_id)
    if not path:
        raise HTTPException(status_code=404, detail="No icon for this plugin.")
    media_type, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=media_type or "application/octet-stream")
