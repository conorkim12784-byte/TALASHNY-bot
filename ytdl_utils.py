# ytdl_utils.py — إعدادات yt-dlp المركزية (معدلة بالكامل لحل مشاكل يوتيوب)

import os

COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

COMMON = {
    "cookiefile": COOKIES_FILE,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "geo_bypass": True,
    "geo_bypass_country": "US",
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"],
            "skip": ["hls", "dash"]
        }
    },
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    },
    "sleep_interval": 2,
    "max_sleep_interval": 5,
}


def audio_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s") -> dict:
    return {
        **COMMON,
        "format": "bestaudio/best",
        "outtmpl": out_tpl,
    }


def video_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s", height: int = 720) -> dict:
    return {
        **COMMON,
        "format": f"bestvideo[height<={height}]+bestaudio/best/best",
        "outtmpl": out_tpl,
        "merge_output_format": "mp4",
    }


def stream_opts(fmt: str = "bestaudio/best") -> dict:
    return {
        **COMMON,
        "format": fmt,
        "skip_download": True,
    }
