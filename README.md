# ChannelDown

I coded this for personal use and deceided why not reveal it to the public. Stuff like the resolution and the amount of new vids to download is now configurable from the launcher menu instead of being hardcoded. Also, dont bug me for it, buuut the readme file is entirely AI since i really cant be bothered to type all that. So here ya go:

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



⚙️ Settings menu (resolution, videos per channel, retries, cooldown, paths)



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

settings.py    # Settings menu + defaults

Launcher.bat



Use the included BAT launcher:



Code

Launcher.bat

This ensures the working directory is correct so logs, state files, and channel lists load properly.



Settings

Run Launcher.bat and pick "2. Settings". You can change:



Max video resolution (144 up to 2160, or best)

Newest videos to check per channel

Retries per failed step and seconds between retries

Cooldown between videos of the same channel

Minimum valid file size (MB)

Output folder for the per-channel subfolders

Paths to yt-dlp.exe, ffmpeg and ffprobe



Choosing "s" saves the values to settings.json and starts the downloader straight away; "q" goes back without saving. Anything not present in settings.json falls back to the defaults in settings.py.



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

Launcher (Launcher.bat)

Included in the repo. It cds into the script folder and shows a menu:



Code

1. Start downloading

2. Settings (resolution, videos per channel, ...)

3. Exit

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

