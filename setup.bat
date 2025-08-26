@echo off
echo ================================================
echo    Face Recognition Login System Setup
echo ================================================
echo.

REM Check if Python is installed
echo [1/6] Checking Python installation...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python first:
    echo 1. Go to https://www.python.org/downloads/
    echo 2. Download Python 3.11 or later
    echo 3. During installation, check "Add Python to PATH"
    echo 4. Run this script again after installation
    echo.
    pause
    exit /b 1
)
echo Python is installed successfully!

REM Check if pip is available
echo [2/6] Checking pip installation...
py -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not available!
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)
echo pip is available!

REM Create virtual environment
echo [3/6] Creating virtual environment...
if not exist "face_login_env" (
    py -m venv face_login_env
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists!
)

REM Activate virtual environment
echo [4/6] Activating virtual environment...
call face_login_env\Scripts\activate

REM Upgrade pip
echo [5/6] Upgrading pip...
py -m pip install --upgrade pip

REM Install requirements
echo [6/6] Installing required packages...
echo This may take several minutes, please wait...
py -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install some packages!
    echo.
    echo Common solutions:
    echo 1. Install Microsoft Visual C++ Build Tools
    echo 2. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo 3. Select "C++ build tools" workload during installation
    echo 4. Run this script again after installation
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo           Setup Completed Successfully!
echo ================================================
echo.
echo To run the application:
echo 1. Activate virtual environment: face_login_env\Scripts\activate
echo 2. Run the application: python app.py
echo 3. Open browser to: http://localhost:5000
echo.
echo Note: Make sure your camera is connected and working!
echo.
pause
