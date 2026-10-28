@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-win\Scripts\python.exe" goto missing
".venv-win\Scripts\python.exe" main.py --data-dir "%LOCALAPPDATA%\StarGate-Source"
if errorlevel 1 goto failed
exit /b 0
:missing
echo Jalankan SETUP-WINDOWS.cmd terlebih dahulu.
:failed
pause
exit /b 1
