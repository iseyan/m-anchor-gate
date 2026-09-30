@echo off
setlocal
cd /d "%~dp0"
py -3.13 prepare_local.py
set "PREPARATION_EXIT_CODE=%ERRORLEVEL%"
echo.
echo Preparation exit code: %PREPARATION_EXIT_CODE%
pause
exit /b %PREPARATION_EXIT_CODE%
