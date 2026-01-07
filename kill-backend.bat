@echo off
echo Killing backend processes...
taskkill /F /IM uvicorn.exe 2>nul
taskkill /F /IM python.exe 2>nul
echo Done.
pause
