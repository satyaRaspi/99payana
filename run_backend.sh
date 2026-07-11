#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/backend"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
