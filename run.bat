@echo off
echo ================================================
echo  MITM Placement Dashboard - Setup ^& Run Script
echo  Powered by uv (Python package manager)
echo ================================================
echo.

set UV="C:\Users\User\.local\bin\uv.exe"

REM Check uv exists
if not exist %UV% (
    echo [ERROR] uv not found. Installing...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
)

echo [1/3] Installing dependencies with uv...
%UV% pip install -r requirements.txt --python 3.11 2>&1
if errorlevel 1 (
    echo Trying with Python 3.12...
    %UV% pip install -r requirements.txt --python 3.12 2>&1
)
echo [OK] Dependencies installed.

echo.
echo [2/3] Seeding database with MITM demo data...
%UV% run --python 3.11 python -m app.seed 2>&1
echo [OK] Database seeded.

echo.
echo [3/3] Starting MITM Placement Dashboard...
echo.
echo  =================================================
echo   Open in browser: http://127.0.0.1:8000
echo  =================================================
echo   Admin Login:   http://127.0.0.1:8000/admin/login
echo   Student Login: http://127.0.0.1:8000/student/login
echo  -------------------------------------------------
echo   ADMIN  - Email: admin.in@mitm.ac.in
echo   ADMIN  - Pass:  Admin@1234
echo   STUDENT- Mobile: 9876543210  (OTP shown in console)
echo  =================================================
echo.
echo  Press Ctrl+C to stop.
echo.

%UV% run --python 3.11 uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
