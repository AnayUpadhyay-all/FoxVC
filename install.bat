@echo off
setlocal

echo ========================================================
echo   Installing FoxVC v0.5.2x for Windows
echo ========================================================

:: Check Python availability
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python from https://python.org and check "Add to PATH".
    pause
    exit /b 1
)

:: Target user bin folder
set "FOX_DIR=%~dp0"
set "TARGET_DIR=%LOCALAPPDATA%\Microsoft\WindowsApps"

:: Create foxvc.cmd shim in default WindowsApps PATH
echo @echo off > "%TARGET_DIR%\foxvc.cmd"
echo python "%FOX_DIR%engine\cli.py" %%* >> "%TARGET_DIR%\foxvc.cmd"

echo.
echo ========================================================
echo   [SUCCESS] FoxVC installed successfully!
echo   Open Command Prompt / PowerShell and type: foxvc
echo ========================================================
pause
