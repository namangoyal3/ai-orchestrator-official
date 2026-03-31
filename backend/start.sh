#!/bin/bash
set -e
# Ensure uvicorn is available (Railpack doesn't install it from requirements)
pip install uvicorn[standard] --quiet 2>/dev/null || true
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
