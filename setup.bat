@echo off
title YouTube Downloader Setup (No Admin)
echo ===========================================
echo   Setting up tools in C:\Tools (no admin)
echo ===========================================
echo.

REM -------------------------------------------
REM Define install directory
REM -------------------------------------------
set "BASE=C:\Tools"
set "YTDLP=%BASE%\yt-dlp"
set "FFMPEG=%BASE%\ffmpeg"

echo Installing to: %BASE%
mkdir "%YTDLP%" >nul 2>&1
mkdir "%FFMPEG%" >nul 2>&1

REM -------------------------------------------
REM Download yt-dlp.exe (portable)
REM -------------------------------------------
echo Downloading yt-dlp.exe...
powershell -Command "(New-Object Net.WebClient).DownloadFile('https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe','%YTDLP%\yt-dlp.exe')"

if not exist "%YTDLP%\yt-dlp.exe" (
    echo ERROR: Failed to download yt-dlp.exe
    pause
    exit /b
)

echo yt-dlp installed successfully.
echo.

REM -------------------------------------------
REM Download FFmpeg portable build (no admin)
REM -------------------------------------------
echo Downloading FFmpeg portable...
powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip','ffmpeg.zip')"

if not exist "ffmpeg.zip" (
    echo ERROR: Failed to download FFmpeg.
    pause
    exit /b
)

echo Extracting FFmpeg...
powershell -Command "Expand-Archive -Path ffmpeg.zip -DestinationPath ffmpeg_temp -Force"

for /d %%i in (ffmpeg_temp\*) do (
    xcopy "%%i\bin" "%FFMPEG%" /e /i /y >nul
)

del ffmpeg.zip >nul 2>&1
rmdir /s /q ffmpeg_temp >nul 2>&1

echo FFmpeg installed successfully.
echo.

REM -------------------------------------------
REM Add tools to PATH for this session only
REM -------------------------------------------
set PATH=%PATH%;%YTDLP%;%FFMPEG%
echo Tools added to PATH for this session.
echo.

REM -------------------------------------------
REM Create downloaded.txt if missing
REM -------------------------------------------
if not exist downloaded.txt (
    echo Creating downloaded.txt...
    type nul > downloaded.txt
)

echo downloaded.txt ready.
echo.

REM -------------------------------------------
REM Verification
REM -------------------------------------------
echo Checking yt-dlp:
"%YTDLP%\yt-dlp.exe" --version
echo.

echo Checking FFmpeg:
"%FFMPEG%\ffmpeg.exe" -version
echo.

echo ===========================================
echo Setup complete!
echo Run your Python script from this window.
echo ===========================================
pause