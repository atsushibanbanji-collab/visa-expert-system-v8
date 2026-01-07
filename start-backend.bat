@echo off
echo Starting Backend...
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
uvicorn main:app --reload --host 0.0.0.0 --port 8000
