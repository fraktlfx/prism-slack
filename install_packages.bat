@echo off
setlocal

REM Ensure script runs from a local mapped path even when launched from a UNC share
pushd "%~dp0" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not access script directory: %~dp0
    pause
    exit /b 1
)

title Slack Plugin Python Package Installer

REM Get directory of this bat file
set BASE_DIR=%~dp0
set TARGET_DIR=%BASE_DIR%PythonLibs
set "PYTHON_EXE="

if exist "C:\Program Files\Prism2\Python313\python.exe" set "PYTHON_EXE=C:\Program Files\Prism2\Python313\python.exe" && echo Found Python 3.13 at C:\Program Files\Prism2\Python313\python.exe && set PY_VERSION=3.13
if not defined PYTHON_EXE if exist "C:\Program Files\Prism2\Python311\python.exe" set "PYTHON_EXE=C:\Program Files\Prism2\Python311\python.exe" && echo Found Python 3.11 at C:\Program Files\Prism2\Python311\python.exe && set PY_VERSION=3.11

if not defined PYTHON_EXE (
    set "PRISM_DIR="
    set /p PRISM_DIR=No supported python executable found. Enter your Prism2 installation directory ^(example: C:\Program Files\Prism2^): 
    if exist "%PRISM_DIR%\Python313\python.exe" set "PYTHON_EXE=%PRISM_DIR%\Python313\python.exe" && echo Found Python 3.13 at %PRISM_DIR%\Python313\python.exe && set PY_VERSION=3.13
    if not defined PYTHON_EXE if exist "%PRISM_DIR%\Python311\python.exe" set "PYTHON_EXE=%PRISM_DIR%\Python311\python.exe" && echo Found Python 3.11 at %PRISM_DIR%\Python311\python.exe && set PY_VERSION=3.11
)

if not defined PYTHON_EXE (
    echo ERROR: Could not find supported python.exe in the provided Prism2 directory.
    pause
    exit /b 1
)

echo.
echo ================================
echo Installing Python packages locally
echo Target: %TARGET_DIR%
echo Prism Python: %PYTHON_EXE%
echo Required compatible version: %PY_VERSION%
echo ================================
echo.

REM Ensure Prism Python exists
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Prism python executable is not runnable: %PYTHON_EXE%
    pause
    exit /b 1
)

REM Ensure py launcher exists with matching version
py -%PY_VERSION% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not find system Python %PY_VERSION% via the py launcher.
    echo Please install Python %PY_VERSION% for Windows and make sure the py launcher is available.
    pause
    exit /b 1
)

echo ================================
echo Installing Python packages locally
echo Target: %TARGET_DIR%
echo ================================
echo.


REM Create target directory if needed
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
)

REM Install packages locally
py -%PY_VERSION% -m pip install ^
    --target "%TARGET_DIR%" ^
    slack_sdk ^
    slack_bolt

IF ERRORLEVEL 1 (
    echo ERROR: Package installation failed.
    pause
    exit /b 1
)

echo.
echo ================================
echo Installation complete!
echo Packages installed to:
echo %TARGET_DIR%
echo ================================
pause

popd >nul 2>&1
