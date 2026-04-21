@echo off
REM Build script for ADB Manager Pro
REM Creates a standalone EXE installer

echo.
echo ========================================
echo  ADB Manager Pro - Build Installer
echo ========================================
echo.

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

echo.
echo Building executable...
echo.

REM Build the executable
pyinstaller --onefile --windowed --name "ADB_Manager_Pro" --icon=NONE ^
    --hidden-import=PyQt5.sip ^
    --hidden-import=database ^
    --hidden-import=device_manager ^
    --hidden-import=tool_manager ^
    --hidden-import=config ^
    main.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo Output location: dist/ADB_Manager_Pro.exe
echo.
pause
