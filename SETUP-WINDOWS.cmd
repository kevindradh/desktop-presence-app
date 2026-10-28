@echo off
setlocal
cd /d "%~dp0"
if defined SG_SOURCE_PYTHON goto custom_python
py -3.11 scripts\setup_source_windows.py %*
goto finished
:custom_python
"%SG_SOURCE_PYTHON%" scripts\setup_source_windows.py %*
:finished
if errorlevel 1 goto failed
echo Setup berhasil.
if not defined SG_SOURCE_NO_PAUSE pause
exit /b 0
:failed
echo Setup gagal. Periksa pesan di atas. Python 3.11 x64 dan Visual C++ Runtime x64 harus tersedia.
if not defined SG_SOURCE_NO_PAUSE pause
exit /b 1
