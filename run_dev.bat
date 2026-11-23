@echo off
title DocuChat AI - Dev Mode (FastAPI + Vite)
echo ========================================================
echo        Starting DocuChat AI in Live Development Mode
echo ========================================================
echo.
echo Launching FastAPI Backend on http://localhost:8000...
start cmd /k "title DocuChat Backend && cd /d %~dp0backend && python main.py"

echo Launching Vite React Dev Server on http://localhost:5173...
start cmd /k "title DocuChat Frontend && cd /d %~dp0frontend && npm run dev"

echo.
echo Both servers started in background terminals!
echo Opening Frontend in browser...
timeout /t 3 >nul
start http://localhost:5173
