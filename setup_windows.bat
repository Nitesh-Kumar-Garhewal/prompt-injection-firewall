@echo off
setlocal
cd /d %~dp0

echo === Setting up backend ===
cd backend
py -3 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env >nul
cd ..

echo === Setting up frontend ===
cd frontend
npm install
cd ..

echo.
echo Setup complete.
echo Start backend with start_backend.bat
 echo Start frontend with start_frontend.bat
