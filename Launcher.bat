@echo off
REM === Change to script directory ===
cd /d "%~dp0"

REM === Optional: create log folder ===
if not exist logs mkdir logs

REM === Run the downloader ===
python "yt download.py"

pause
