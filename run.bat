@echo off
echo ================================================
echo      Face Recognition Login System
echo ================================================
echo.

REM Check if virtual environment exists
if not exist "face_login_env" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call face_login_env\Scripts\activate

REM Check if app.py exists
if not exist "app.py" (
    echo ERROR: app.py not found!
    echo Please ensure you're in the correct directory.
    echo.
    pause
    exit /b 1
)

echo Starting Face Recognition Login System...
echo.
echo Application will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Run the application
python app.py
