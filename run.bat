@echo off
title SNAP DISAPPEAR - Real-Time Avengers Dust VFX
echo =====================================================================
echo           SNAP DISAPPEAR - REAL-TIME AVENGERS DUST EFFECT
echo =====================================================================
echo.
echo Launching application...
python main.py
if errorlevel 1 (
    echo.
    echo An error occurred while launching. Press any key to exit.
    pause >nul
)

