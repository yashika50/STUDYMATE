@echo off
echo ============================================
echo   StudyMate - Starting up...
echo ============================================
echo.

:: Install dependencies
echo [1/2] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies. Make sure Python and pip are installed.
    pause
    exit /b 1
)

echo.
echo [2/2] Launching StudyMate...
echo The app will open at http://localhost:8501
echo Press Ctrl+C to stop the app.
echo.
streamlit run app.py
