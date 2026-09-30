@echo off
setlocal
set "GATE_PYTHON=C:\Users\ise\Desktop\schema-gate-003-local-preparation-v0.1\environments\local-preparation-20260930T102507Z-5db00b37\Scripts\python.exe"
set "GATE_SCRIPT=%~dp0run_schema_gate_003.py"
if not exist "%GATE_PYTHON%" (
  echo The confirmed Python environment was not found.
  echo Keep the extracted preparation kit at its original location.
  pause
  exit /b 2
)
if not exist "%GATE_SCRIPT%" (
  echo Save run_schema_gate_003.py in the same folder as this CMD file.
  pause
  exit /b 2
)
echo Running schema-gate-003 with the confirmed Python environment...
"%GATE_PYTHON%" -I -B -X utf8 "%GATE_SCRIPT%"
set "GATE_EXIT=%ERRORLEVEL%"
echo.
echo Launcher exit code: %GATE_EXIT%
echo Keep the output ZIP, including any failure record.
pause
exit /b %GATE_EXIT%
