# Railpack entrypoint — imports must be here so Railpack detects all dependencies
import uvicorn  # noqa: F401 — required so Railpack includes uvicorn in the venv
from app.main import app  # noqa: F401
