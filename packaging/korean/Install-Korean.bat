@echo off
setlocal

fltmc >nul 2>&1
if errorlevel 1 (
    echo Requesting administrator privileges...
    powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-korean.ps1" %*
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%"=="0" (
    echo Korean OpenMW installation completed successfully.
) else (
    echo Korean OpenMW installation failed with exit code %EXITCODE%.
)

pause
exit /b %EXITCODE%
