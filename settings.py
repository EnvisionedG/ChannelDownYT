"""User settings for ChannelDown.

Settings live in settings.json next to this file. Run this module directly
(or pick "Settings" in Launcher.bat) to edit them from a console menu.
"""

import json
import os
from typing import Any, Dict, List

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

RESOLUTIONS = ["144", "240", "360", "480", "720", "1080", "1440", "2160", "best"]

DEFAULTS: Dict[str, Any] = {
    "resolution": "360",
    "newest_per_channel": 2,
    "max_retries": 5,
    "retry_delay": 5,
    "channel_cooldown": 30,
    "min_file_size_mb": 1,
    "output_dir": ".",
    "ytdlp_path": r"C:\Tools\yt-dlp\yt-dlp.exe",
    "ffmpeg_path": "ffmpeg",
    "ffprobe_path": "ffprobe",
}


def load_settings() -> Dict[str, Any]:
    settings = dict(DEFAULTS)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                stored = json.load(f)
            if isinstance(stored, dict):
                settings.update({k: v for k, v in stored.items() if k in DEFAULTS})
        except (OSError, json.JSONDecodeError) as e:
            print(f"Could not read {SETTINGS_FILE} ({e}); using defaults.")
    return settings


def save_settings(settings: Dict[str, Any]) -> None:
    tmp = SETTINGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, SETTINGS_FILE)


def build_format_chain(resolution: str) -> List[str]:
    """yt-dlp format selectors, best first, falling back to anything playable."""
    if str(resolution).lower() == "best":
        return ["bv*[ext=mp4]+ba[ext=m4a]", "bv*+ba", "b[ext=mp4]", "best"]

    height = str(resolution)
    return [
        f"bv*[height<={height}][ext=mp4]+ba[ext=m4a]",
        f"bv*[height<={height}]+ba",
        f"b[height<={height}][ext=mp4]",
        f"b[height<={height}]",
        "best",
    ]


# ===========================
# CONSOLE MENU
# ===========================

_FIELDS = [
    ("resolution", "Max video resolution", "choice"),
    ("newest_per_channel", "Newest videos to check per channel", "int"),
    ("max_retries", "Retries per failed step", "int"),
    ("retry_delay", "Seconds between retries", "int"),
    ("channel_cooldown", "Seconds to wait between videos of one channel", "int"),
    ("min_file_size_mb", "Minimum valid file size (MB)", "int"),
    ("output_dir", "Folder for channel subfolders", "text"),
    ("ytdlp_path", "Path to yt-dlp.exe", "text"),
    ("ffmpeg_path", "ffmpeg command or path", "text"),
    ("ffprobe_path", "ffprobe command or path", "text"),
]


def _prompt_int(label: str, current: int) -> int:
    while True:
        raw = input(f"{label} [{current}]: ").strip()
        if not raw:
            return current
        try:
            value = int(raw)
        except ValueError:
            print("  Enter a whole number.")
            continue
        if value < 1:
            print("  Must be at least 1.")
            continue
        return value


def _prompt_text(label: str, current: str) -> str:
    raw = input(f"{label} [{current}]: ").strip().strip('"')
    return raw or current


def _prompt_resolution(current: str) -> str:
    print("  Options: " + ", ".join(RESOLUTIONS))
    while True:
        raw = input(f"Max video resolution [{current}]: ").strip().lower().rstrip("p")
        if not raw:
            return current
        if raw in RESOLUTIONS:
            return raw
        print("  Pick one of: " + ", ".join(RESOLUTIONS))


def _print_settings(settings: Dict[str, Any]) -> None:
    print()
    print("=== ChannelDown settings ===")
    for index, (key, label, _kind) in enumerate(_FIELDS, start=1):
        print(f" {index:>2}. {label}: {settings[key]}")
    print("  s. Save and start downloading")
    print("  r. Reset to defaults")
    print("  q. Quit without saving")
    print()


def run_menu() -> int:
    """Returns 0 if the caller should start the downloader, 1 otherwise."""
    settings = load_settings()
    while True:
        _print_settings(settings)
        choice = input("Choose an option: ").strip().lower()

        if choice == "q":
            return 1
        if choice == "r":
            settings = dict(DEFAULTS)
            print("Reset to defaults (not saved yet).")
            continue
        if choice == "s":
            save_settings(settings)
            print(f"Saved to {SETTINGS_FILE}")
            return 0
        if not choice.isdigit() or not 1 <= int(choice) <= len(_FIELDS):
            print("Unknown option.")
            continue

        key, label, kind = _FIELDS[int(choice) - 1]
        if kind == "int":
            settings[key] = _prompt_int(label, settings[key])
        elif kind == "choice":
            settings[key] = _prompt_resolution(settings[key])
        else:
            settings[key] = _prompt_text(label, settings[key])


if __name__ == "__main__":
    raise SystemExit(run_menu())
