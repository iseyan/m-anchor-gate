@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"

py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 goto use_py
python -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 goto use_python

echo Python 3.10 or later was not found. No installation was attempted.
set "STAGE4_DEMO_EXIT=1"
goto finish

:use_py
py -3 -B -X utf8 "%~dp0prototype\run_demo.py" %*
set "STAGE4_DEMO_EXIT=%ERRORLEVEL%"
goto finish

:use_python
python -B -X utf8 "%~dp0prototype\run_demo.py" %*
set "STAGE4_DEMO_EXIT=%ERRORLEVEL%"

:finish
echo.
echo Demo exit code: %STAGE4_DEMO_EXIT%
pause
exit /b %STAGE4_DEMO_EXIT%
