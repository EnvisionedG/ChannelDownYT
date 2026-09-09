# YT

I coded this for personal use and deceided why not reveal it to the public, i have got hardcoded stuff, like the resolution, and the amount of new vids to download and such. Also, dont bug me for it, buuut the readme file is entirely AI since i really cant be bothered to type all that. So here ya go:

ChannelDown

A fast, resilient, multi‑channel YouTube downloader powered by yt‑dlp, FFmpeg, and a custom Python orchestration layer.

ChannelDown automatically checks your subscribed channels, fetches the newest uploads, downloads them with fallback formats, validates the files, and organizes everything into tidy channel folders.



It’s built for reliability, automation, and long‑term unattended operation.



Features

🔍 Auto‑detect newest videos from each channel



📥 Multiple fallback formats (DASH, progressive, best)



🧪 Download validation using FFprobe (duration, size, corruption checks)



🔁 Automatic retry system with cooldowns



🧹 Corrupted file quarantine



📂 Organized output into per‑channel folders



🛑 STOP file support for safe shutdown



🧵 Graceful Ctrl+C handling



🔧 Self‑repairing yt‑dlp.exe (auto‑redownload if missing or corrupted)



Requirements

Python 3.10+



FFmpeg + FFprobe in PATH



yt‑dlp.exe (auto‑download supported)



Windows (script is Windows‑optimized)



Installation

Clone the repo:



Code

git clone https://github.com/EnvisionedG/ChannelDown

cd ChannelDown

Ensure the following files exist:



Code

channels.txt   # List of YouTube channel URLs or @handles

skip.txt       # Optional: video IDs to skip

yt download.py # Main script

run\_downloader.bat



Use the included BAT launcher:



Code

run\_downloader.bat

This ensures the working directory is correct so logs, state files, and channel lists load properly.



Add channels

Edit channels.txt:



Code

https://www.youtube.com/@SomeChannel

https://www.youtube.com/channel/UC1234567890abcdef

Handles and full channel URLs are supported.



Skip videos

Add video IDs to skip.txt:



Code

dQw4w9WgXcQ

How It Works

1\. Channel scanning

The script fetches the newest videos from each channel using yt‑dlp’s playlist JSON dump.



2\. Download queue building

Videos are sorted by timestamp and processed newest‑first.



3\. Multi‑format fallback

If one format fails, ChannelDown tries the next until success.



4\. FFmpeg download with live progress

Includes ETA, speed, percent, and duration tracking.



5\. Validation

Files are checked for:



Minimum size



Duration accuracy



FFprobe readability



Invalid files are moved to /corrupted.



6\. Organized output

Videos are saved as:



Code

ChannelName/YYYY-MM-DD - Title.mp4

Launcher (run\_downloader.bat)

Included in the repo:



Code

@echo off

cd /d "%\~dp0"

python "yt download.py"

pause

This prevents Windows from running the script inside C:\\Windows\\System32, which causes permission errors.



Contributing

Pull requests are welcome!

If you want to add features like:



GUI



Auto‑update channels



Discord webhook notifications



Scheduled background service



Feel free to open an issue or PR.



License

MIT License — do whatever you want with it

