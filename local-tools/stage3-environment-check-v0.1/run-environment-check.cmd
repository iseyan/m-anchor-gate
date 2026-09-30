@echo off
setlocal
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
set "ENTRY_PYTHON=C:\Users\ise\Desktop\schema-gate-003-local-preparation-v0.1\environments\local-preparation-20260930T102507Z-5db00b37\Scripts\python.exe"
if not "%~1"=="" set "ENTRY_PYTHON=%~1"
if not exist "%ENTRY_PYTHON%" goto missing
"%ENTRY_PYTHON%" -I -B -X utf8 "%~dp0run_environment_check.py" --python "%ENTRY_PYTHON%"
set "ENTRY_EXIT=%ERRORLEVEL%"
echo.
echo Finished with exit code %ENTRY_EXIT%. A check result does not authorize a live run.
pause
exit /b %ENTRY_EXIT%
:missing
echo Recorded Python was not found:
echo %ENTRY_PYTHON%
echo No check was started. No package was installed.
echo Supply the actual venv python.exe as the first argument. See README.ja.md.
pause
exit /b 2
