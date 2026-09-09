import subprocess
import json
import os
import re
import time
import shutil
import logging
from typing import Dict, Any, List, Optional
import signal
import sys
import time

def format_time(seconds: float) -> str:
    if seconds is None or seconds <= 0:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m:02d}m {s:02d}s"
# ===========================
# YT-DLP SELF CHECK
# ===========================

def verify_ytdlp() -> bool:
    """
    Ensures yt-dlp.exe exists, is the correct size, and is runnable.
    If invalid, attempts automatic re-download.
    Returns True if usable, False if fatal.
    """
    expected_min_size = 5_000_000  # 5 MB sanity check

    # 1. Check existence
    if not os.path.exists(YTDLP):
        logging.error("yt-dlp.exe missing at %s", YTDLP)
        return attempt_redownload()

    # 2. Check file size
    size = os.path.getsize(YTDLP)
    if size < expected_min_size:
        logging.error("yt-dlp.exe is too small (%d bytes) — likely corrupted.", size)
        return attempt_redownload()

    # 3. Check if executable runs
    try:
        test = subprocess.run([YTDLP, "--version"],
                              capture_output=True, text=True)
        if test.returncode != 0:
            logging.error("yt-dlp.exe failed to run (code %d).", test.returncode)
            return attempt_redownload()
    except Exception as e:
        logging.error("yt-dlp.exe failed to execute: %s", e)
        return attempt_redownload()

    logging.info("yt-dlp.exe verified OK (size=%d bytes)", size)
    return True


def attempt_redownload() -> bool:
    """
    Attempts to re-download yt-dlp.exe automatically.
    """
    logging.warning("Attempting to re-download yt-dlp.exe...")

    try:
        import urllib.request
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

        ensure_dir(os.path.dirname(YTDLP))
        urllib.request.urlretrieve(url, YTDLP)

        size = os.path.getsize(YTDLP)
        logging.info("Downloaded new yt-dlp.exe (%d bytes)", size)

        return size > 5_000_000
    except Exception as e:
        logging.error("Failed to download yt-dlp.exe: %s", e)
        return False


# ===========================
# GLOBAL INTERRUPT FLAG
# ===========================

INTERRUPTED = False

def handle_sigint(signum, frame):
    global INTERRUPTED
    INTERRUPTED = True
    print("\n\n[!] Ctrl+C detected — finishing current task safely...")
    logging.warning("Ctrl+C detected — graceful shutdown requested.")

signal.signal(signal.SIGINT, handle_sigint)

# ===========================
# CONFIG
# ===========================

CHANNEL_FILE = "channels.txt"

def load_channels() -> List[str]:
    if not os.path.exists(CHANNEL_FILE):
        print(f"Channel file '{CHANNEL_FILE}' not found.")
        return []

    channels: List[str] = []
    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            channels.append(line)
    return channels
SKIP_FILE = "skip.txt"

def load_skip_list() -> set:
    if not os.path.exists(SKIP_FILE):
        return set()
    ids = set()
    with open(SKIP_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            ids.add(line)
    return ids
SKIP_LIST = load_skip_list()    
CHANNELS = load_channels()

YTDLP = r"C:\Tools\yt-dlp\yt-dlp.exe"
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

STATE_FILE = "state.json"
CORRUPTED_DIR = "corrupted"
STOP_FILE = "STOP"
LOG_FILE = "downloader.log"

MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds
CHANNEL_COOLDOWN = 30  # seconds between hits to same channel
MIN_FILE_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB
NEWEST_PER_CHANNEL = 2

FORMAT_CHAIN = [
    "134+140",  # 360p DASH
    "18",       # 360p progressive
    "93",
    "92",
    "91",
    "best"
]

# ===========================
# LOGGING (file + console)
# ===========================

logger = logging.getLogger()
logger.setLevel(logging.INFO)

fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

logger.addHandler(fh)
logger.addHandler(ch)

# ===========================
# UTILS
# ===========================

def sanitize(name: str) -> str:
    if not name:
        return "Unknown"
    name = str(name)
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    return name.strip().rstrip('.')

def extract_channel_name_from_url(url: str) -> str:
    # Handles @handles and /channel/UCxxxx
    name = url.rstrip("/").split("/")[-1]
    name = name.replace("@", "")
    return sanitize(name or "UnknownChannel")

def run_subprocess(cmd: List[str], desc: str,
                   capture_output: bool = True,
                   text: bool = True) -> subprocess.CompletedProcess:
    logging.info("RUN %s: %s", desc, " ".join(cmd))
    return subprocess.run(cmd, capture_output=capture_output, text=text)


def run_with_retries(cmd: List[str], desc: str, max_retries: int = MAX_RETRIES,
                     retry_delay: int = RETRY_DELAY, capture_output: bool = True,
                     text: bool = True) -> Optional[subprocess.CompletedProcess]:
    for attempt in range(1, max_retries + 1):
        if INTERRUPTED:
            logging.warning("[%s] Aborting retries due to interrupt.", desc)
            return None
        logging.info("[%s] Attempt %d/%d", desc, attempt, max_retries)
        result = run_subprocess(cmd, desc, capture_output=capture_output, text=text)
        if result.returncode == 0:
            return result
        logging.warning("[%s] Failed (code %d).", desc, result.returncode)
        if attempt < max_retries:
            logging.info("[%s] Retrying in %d seconds...", desc, retry_delay)
            time.sleep(retry_delay)
    logging.error("[%s] All %d attempts failed.", desc, max_retries)
    return None


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def check_stop() -> bool:
    return os.path.exists(STOP_FILE)

# ===========================
# STATE MANAGER (atomic JSON)
# ===========================

def load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        return {
            "downloaded": [],
            "in_progress": None,
            "last_checked": {},
            "cooldowns": {}
        }
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error("Failed to load state file: %s", e)
        return {
            "downloaded": [],
            "in_progress": None,
            "last_checked": {},
            "cooldowns": {}
        }


def save_state(state: Dict[str, Any]) -> None:
    tmp = STATE_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        logging.error("Failed to save state file: %s", e)


def mark_downloaded(state: Dict[str, Any], video_id: str) -> None:
    if video_id not in state["downloaded"]:
        state["downloaded"].append(video_id)
    if state.get("in_progress") == video_id:
        state["in_progress"] = None
    save_state(state)

# ===========================
# YOUTUBE METADATA / FETCH
# ===========================

def get_latest_videos_for_channel(channel_url: str) -> List[Dict[str, Any]]:
    cmd = [
        YTDLP,
        "--dump-json",
        "--flat-playlist",
        "--extractor-args", "youtube:skip=dash",
        f"{channel_url}/videos"
    ]

    result = run_with_retries(cmd, f"playlist:{channel_url}")
    if not result or not result.stdout:
        return []

    videos: List[Dict[str, Any]] = []
    for line in result.stdout.splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        if data.get("_type") != "url":
            continue

        vid = data.get("id")
        if not vid:
            continue

        title = data.get("title") or "Untitled"
        channel = extract_channel_name_from_url(channel_url)
        upload_date = data.get("upload_date") or None
        duration = data.get("duration") or None
        timestamp = data.get("timestamp") or None

        videos.append({
            "id": vid,
            "title": title,
            "channel": channel,
            "upload_date": upload_date,
            "duration": duration,
            "timestamp": timestamp
        })

        if len(videos) >= NEWEST_PER_CHANNEL:
            break

    return videos


def build_download_queue() -> List[Dict[str, Any]]:
    all_videos: List[Dict[str, Any]] = []
    for ch in CHANNELS:
        vids = get_latest_videos_for_channel(ch)
        logging.info("Channel %s -> %d videos", ch, len(vids))
        all_videos.extend(vids)

    def sort_key(v: Dict[str, Any]):
        ts = v.get("timestamp")
        if ts is not None:
            return ts
        ud = v.get("upload_date")
        if ud:
            try:
                return int(ud)
            except ValueError:
                pass
        return 0

    all_videos.sort(key=sort_key, reverse=True)
    return all_videos

# ===========================
# URL FETCH WITH FALLBACK FORMATS
# ===========================

def get_ffmpeg_urls(video_id: str) -> Optional[List[str]]:
    for fmt in FORMAT_CHAIN:
        if INTERRUPTED:
            logging.warning("Interrupted before getting URLs for %s", video_id)
            return None
        cmd = [
            YTDLP,
            "-g",
            "-f", fmt,
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        result = run_with_retries(cmd, f"urls:{video_id}:{fmt}")
        if result and result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.splitlines()
            logging.info("Got URLs for %s with format %s", video_id, fmt)
            return lines
        logging.warning("Format %s failed for %s", fmt, video_id)
    logging.error("All formats failed for %s", video_id)
    return None

# ===========================
# FFMPEG PROGRESS + DOWNLOAD
# ===========================
def kill_ffprobe_locks(path: str):
    """Force-close ffprobe handles on Windows."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "ffprobe.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
        
def parse_ffmpeg_progress_line(line: str) -> Dict[str, str]:
    line = line.strip()
    if "=" not in line:
        return {}
    k, v = line.split("=", 1)
    return {k.strip(): v.strip()}


def ffmpeg_download_with_progress(video_id: str,
                                  urls: List[str],
                                  out_path: str,
                                  expected_duration: Optional[int]) -> bool:
    if len(urls) == 1:
        video_url = urls[0]
        cmd = [
            FFMPEG,
            "-y",
            "-loglevel", "error",
            "-progress", "pipe:2",
            "-i", video_url,
            "-c", "copy",
            out_path
        ]
    else:
        video_url, audio_url = urls
        cmd = [
            FFMPEG,
            "-y",
            "-loglevel", "error",
            "-progress", "pipe:2",
            "-i", video_url,
            "-i", audio_url,
            "-c", "copy",
            out_path
        ]

    logging.info("Starting ffmpeg for %s: %s", video_id, " ".join(cmd))

    proc = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True,
        bufsize=1
    )

    total_seconds = expected_duration or 0
    last_percent = -1
    start_time = time.time()
    try:
        if proc.stderr is None:
            proc.wait()
            return proc.returncode == 0

        for line in proc.stderr:

            if INTERRUPTED:
                proc.terminate()
                logging.warning("Terminated ffmpeg for %s due to Ctrl+C.", video_id)
                return False

            info = parse_ffmpeg_progress_line(line)
            if not info:
                continue

            if "out_time_ms" in info and total_seconds > 0:
                out_ms = int(info["out_time_ms"])
                cur_sec = out_ms / 1_000_000.0

                # Percent
                percent = max(0, min(100, int((cur_sec / total_seconds) * 100)))

                # ETA
                elapsed = time.time() - start_time
                speed = cur_sec / elapsed if elapsed > 0 else 0
                remaining = (total_seconds - cur_sec) / speed if speed > 0 else None

                # Progress bar
                bar_len = 20
                filled = int((percent / 100) * bar_len)
                bar = "█" * filled + "░" * (bar_len - filled)

                # Output
                print(
                    f"\r[{video_id}] [{bar}] {percent:3d}%  "
                    f"{int(cur_sec)}/{total_seconds}s  "
                    f"ETA {format_time(remaining)}  "
                    f"{speed:4.1f}x",
                    end="",
                    flush=True
                )

            if info.get("progress") == "end":
                break

        proc.wait()
    finally:
        print()  # newline after progress

    logging.info("ffmpeg finished for %s with code %d", video_id, proc.returncode)
    return proc.returncode == 0

# ===========================
# VALIDATION (FFPROBE)
# ===========================

def get_media_duration(path: str) -> Optional[float]:
    cmd = [
        FFPROBE,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]
    result = run_with_retries(cmd, f"ffprobe:{os.path.basename(path)}")
    if not result or result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def validate_download(path: str, expected_duration: Optional[int]) -> bool:
    if not os.path.exists(path):
        logging.error("Validation failed: file does not exist: %s", path)
        return False

    size = os.path.getsize(path)
    if size < MIN_FILE_SIZE_BYTES:
        logging.error("Validation failed: file too small (%d bytes): %s", size, path)
        return False

    actual_duration = get_media_duration(path)
    if actual_duration is None:
        logging.error("Validation failed: could not get duration for %s", path)
        return False

    if expected_duration and expected_duration > 0:

    # Adaptive tolerance based on video length
        if expected_duration < 600:          # <10 minutes
            tolerance = 2
        elif expected_duration < 3600:       # <1 hour
            tolerance = 5
        elif expected_duration < 7200:       # <2 hours
            tolerance = 30
        else:                                # >2 hours
            tolerance = 60

        diff = abs(actual_duration - expected_duration)

        if diff > tolerance:
            logging.error(
                "Validation failed: duration mismatch (expected %.2f, got %.2f, diff %.2f > tolerance %.2f) for %s",
                expected_duration, actual_duration, diff, tolerance, path
            )
            return False

    logging.info("Validation OK for %s (size=%d, duration=%.2f)", path, size, actual_duration)
    return True

# ===========================
# ORGANIZER (CHANNEL FOLDERS)
# ===========================

def build_final_path(base_dir: str, channel_name: str,
                     upload_date: Optional[str], title: str) -> str:
    safe_channel = sanitize(channel_name or "UnknownChannel")
    ensure_dir(safe_channel)

    prefix = ""
    if upload_date and len(upload_date) == 8:
        y = upload_date[0:4]
        m = upload_date[4:6]
        d = upload_date[6:8]
        prefix = f"{y}-{m}-{d} - "

    safe_title = sanitize(title or "Untitled")
    filename = prefix + safe_title + ".mp4"
    return os.path.join(safe_channel, filename)

# ===========================
# RESUME / CORRUPTED HANDLING
# ===========================

def move_to_corrupted(path: str) -> None:
    ensure_dir(CORRUPTED_DIR)
    base = os.path.basename(path)
    dest = os.path.join(CORRUPTED_DIR, base)
    logging.warning("Moving corrupted file %s -> %s", path, dest)
    try:
        shutil.move(path, dest)
    except Exception as e:
        logging.error("Failed to move corrupted file %s: %s", path, e)


def resume_incomplete_files(state: Dict[str, Any]) -> None:
    for fname in os.listdir("."):
        if not fname.lower().endswith(".mp4"):
            continue
        vid_id = os.path.splitext(fname)[0]
        if vid_id in state.get("downloaded", []):
            continue
        path = os.path.abspath(fname)
        logging.info("Found leftover file %s (id=%s), validating...", path, vid_id)
        if validate_download(path, None):
            logging.info("Leftover file %s seems valid but unknown; leaving in place.", path)
        else:
            move_to_corrupted(path)

    in_prog = state.get("in_progress")
    if in_prog:
        temp_name = f"{in_prog}.mp4"
        if not os.path.exists(temp_name):
            logging.info("Clearing in_progress (%s) because temp file missing.", in_prog)
            state["in_progress"] = None
            save_state(state)

# ===========================
# MAIN DOWNLOAD LOGIC
# ===========================

def download_video(state: Dict[str, Any], video: Dict[str, Any]) -> None:
    video_id = video["id"]
    title = video["title"]
    channel = video["channel"]
    upload_date = video.get("upload_date")
    expected_duration = video.get("duration")

    logging.info("Starting download for %s (%s)", video_id, title)

    temp_name = f"{video_id}.mp4"
    if os.path.exists(temp_name):
        logging.info("Removing stale temp file %s", temp_name)
        kill_ffprobe_locks(temp_name)
        os.remove(temp_name)

    state["in_progress"] = video_id
    save_state(state)

    for attempt in range(1, MAX_RETRIES + 1):

        if INTERRUPTED:
            logging.warning("Interrupted during download of %s — aborting safely.", video_id)
            return

        logging.info("Download attempt %d/%d for %s", attempt, MAX_RETRIES, video_id)

        urls = get_ffmpeg_urls(video_id)
        if not urls:
            logging.error("Failed to get URLs for %s", video_id)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            break

        ok = ffmpeg_download_with_progress(video_id, urls, temp_name, expected_duration)
        if not ok:
            logging.error("ffmpeg failed for %s on attempt %d", video_id, attempt)
            if os.path.exists(temp_name):
                move_to_corrupted(temp_name)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            break

        if not validate_download(temp_name, expected_duration):
            move_to_corrupted(temp_name)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            break

        final_path = build_final_path(".", channel, upload_date, title)
        ensure_dir(os.path.dirname(final_path))
        logging.info("Moving %s -> %s", temp_name, final_path)
        try:
            shutil.move(temp_name, final_path)
        except Exception as e:
            logging.error("Failed to move file to final location: %s", e)
            move_to_corrupted(temp_name)
            break

        mark_downloaded(state, video_id)
        logging.info("Download complete for %s", video_id)
        return

    logging.error("All download attempts failed for %s", video_id)
    state["in_progress"] = None
    save_state(state)

def main():
    logging.info("=== START ===")

    if not verify_ytdlp():
        logging.critical("yt-dlp.exe is missing or invalid — cannot continue.")
        return

    state = load_state()
    resume_incomplete_files(state)

    queue = build_download_queue()
    logging.info("Queue size: %d", len(queue))

    cooldowns: Dict[str, float] = state.get("cooldowns", {})

    for video in queue:
        # Hot reload skip list each loop
        global SKIP_LIST
        SKIP_LIST = load_skip_list()

        if video["id"] in SKIP_LIST:
            logging.info("Skipping video %s (%s) — listed in skip.txt", video["id"], video["title"])
            continue
        if INTERRUPTED or check_stop():
            logging.info("Graceful exit requested before next video.")
            break

        vid_id = video["id"]
        title = video["title"]
        channel = video["channel"]

        if vid_id in state.get("downloaded", []):
            logging.info("Skipping already downloaded video %s (%s)", vid_id, title)
            continue

        now = time.time()
        last_time = cooldowns.get(channel, 0)
        since_last = now - last_time
        if since_last < CHANNEL_COOLDOWN:
            wait = CHANNEL_COOLDOWN - since_last
            logging.info("Channel %s cooling down for %.1f seconds", channel, wait)
            time.sleep(wait)

        logging.info("Processing video %s (%s) from channel %s", vid_id, title, channel)
        download_video(state, video)

        cooldowns[channel] = time.time()
        state["cooldowns"] = cooldowns
        save_state(state)

        if check_stop():
            logging.info("STOP file detected after processing video; exiting.")
            break

    logging.info("=== EXIT ===")

if __name__ == "__main__":
    main()