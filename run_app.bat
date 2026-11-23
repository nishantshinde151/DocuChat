@echo off
title DocuChat AI - Full Stack Launcher
echo ========================================================
echo        DocuChat AI: Full-Stack React + FastAPI
echo ========================================================
echo.
echo [1/2] Starting FastAPI Backend on http://localhost:8000...
echo [2/2] Serving React Frontend directly from FastAPI...
echo.
echo Interactive Web App: http://localhost:8000
echo Interactive API Docs (Swagger): http://localhost:8000/docs
echo.
echo Opening browser in 3 seconds...
start http://localhost:8000

cd /d "%~dp0backend"
python main.py
pause
