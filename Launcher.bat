@echo off
REM === Change to script directory ===
cd /d "%~dp0"

REM === Optional: create log folder ===
if not exist logs mkdir logs

:menu
cls
echo ===========================================
echo   ChannelDown
echo ===========================================
echo.
echo   1. Start downloading
echo   2. Settings (resolution, videos per channel, ...)
echo   3. Exit
echo.
set "choice="
set /p "choice=Choose an option: "

if "%choice%"=="1" goto run
if "%choice%"=="2" goto settings
if "%choice%"=="3" goto end
goto menu

:settings
cls
python settings.py
REM === Exit code 0 means "save and start" ===
if errorlevel 1 goto menu
goto run

:run
echo.
python "yt download.py"
echo.
pause
goto menu

:end
