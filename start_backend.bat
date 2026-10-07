@echo off
cd /d %~dp0\backend
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env >nul
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
