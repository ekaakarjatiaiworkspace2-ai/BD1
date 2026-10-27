#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
if ! .venv/bin/python -c 'import fastapi,uvicorn,multipart' >/dev/null 2>&1; then .venv/bin/pip install -r requirements.txt; fi
.venv/bin/python app.py
