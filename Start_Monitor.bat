@echo off
TITLE Svchost Network Monitor Launcher
color 0A

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :menu
) else (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process -FilePath '%~dpnx0' -Verb RunAs"
    exit /b
)

:menu
cd /d "%~dp0"
cls
echo ===================================================================
echo              Svchost Network Monitor - Main Menu
echo ===================================================================
echo.
echo Please choose a monitoring mode:
echo.
echo [1] Ultimate Auto-Pilot Mode (Highly Recommended)
echo     - Uses Sysmon Kernel driver to catch sub-second connections.
echo     - Uses a Time Machine Buffer to never drop a packet.
echo     - No manual IP entry required. Fully automatic.
echo.
echo [2] Standard Auto-Pilot Mode 
echo     - Good for long-running connections without installing Sysmon.
echo.
echo [3] Advanced Mode (Sysmon Alerts Only)
echo     - Best for just reading connection alerts without packet stats.
echo.
echo [4] Packet Counting Mode (Manual Target)
echo     - Shows real-time packet counts via pktmon.
echo.
echo [5] Exit
echo.
set /p choice="Type 1, 2, 3, 4 or 5 and press Enter: "

if "%choice%"=="1" goto ultimate
if "%choice%"=="2" goto autopilot
if "%choice%"=="3" goto advanced
if "%choice%"=="4" goto counting
if "%choice%"=="5" exit
goto menu

:ultimate
cls
echo ====================================================
echo    Running: Ultimate Auto-Pilot
echo ====================================================
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_sysmon.ps1
.venv\Scripts\python.exe monitor_ultimate.py
echo.
pause
goto menu

:autopilot
cls
echo ====================================================
echo    Running: Auto-Pilot Mode (Discovery + Packets)
echo ====================================================
.venv\Scripts\python.exe monitor_autopilot.py
echo.
pause
goto menu

:standard
cls
echo ====================================================
echo    Running: Standard Mode (Polling)
echo ====================================================
.venv\Scripts\python.exe monitor_svchost_live.py
echo.
pause
goto menu

:advanced
cls
echo ====================================================
echo    Running: Advanced Mode (Sysmon Event Tracking)
echo ====================================================
:: We call a PowerShell script to handle the Sysmon download, install, and tailing
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_sysmon_monitor.ps1
echo.
pause
goto menu

:counting
cls
echo ====================================================
echo    Running: Packet Counting Mode (pktmon)
echo ====================================================
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_packet_counter.ps1
echo.
pause
goto menu
