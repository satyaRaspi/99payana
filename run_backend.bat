@echo off
cd /d %~dp0\backend
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
