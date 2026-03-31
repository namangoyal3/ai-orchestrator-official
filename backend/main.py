import os
import sys

# Ensure the directory containing this file is on sys.path so 'app' package is found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn  # noqa: F401 — required so Railpack includes uvicorn in the venv
from app.main import app  # noqa: F401

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
