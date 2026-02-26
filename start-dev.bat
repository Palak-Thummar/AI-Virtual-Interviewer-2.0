@echo off
setlocal

set ROOT=%~dp0
set BACKEND=%ROOT%backend
set FRONTEND=%ROOT%frontend

echo Starting AI Placement Preparation Platform...
echo.

if not exist "%BACKEND%" (
  echo [ERROR] Backend folder not found: %BACKEND%
  exit /b 1
)

if not exist "%FRONTEND%" (
  echo [ERROR] Frontend folder not found: %FRONTEND%
  exit /b 1
)

start "Backend Server" cmd /k "cd /d "%BACKEND%" && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) else (echo [WARN] venv not found - using system Python) && python -m uvicorn app.main:app --reload"

start "Frontend Dev Server" cmd /k "cd /d "%FRONTEND%" && npm run dev"

echo Backend and frontend terminals launched.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo.
echo Close this window or keep it open.
