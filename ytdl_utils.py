# ytdl_utils.py — إعداد مركزي لـ yt-dlp بدون cookies
# الحل هنا يعتمد على PO Token provider المحلي + fallback تلقائي بين عملاء YouTube.

import os
import re
from copy import deepcopy
from pathlib import Path

import yt_dlp

POT_BASE_URL = os.getenv("POT_BASE_URL", "http://127.0.0.1:4416").rstrip("/")

AUDIO_FORMAT = (
    "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio[ext=opus]"
    "/bestaudio/best[acodec!=none]/best/bestaudio*"
)

VIDEO_FORMAT = (
    "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]"
    "/bestvideo[height<=720]+bestaudio/best[height<=720][ext=mp4]"
    "/best[height<=720]/best"
)

COMMON_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}

_STRATEGIES = [
    {
        "label": "pot-web-safari",
        "youtube": {"player_client": ["web_safari"]},
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    },
    {
        "label": "pot-web",
        "youtube": {"player_client": ["web"]},
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    },
    {
        "label": "pot-mweb",
        "youtube": {"player_client": ["mweb"]},
        "ua": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    },
    {
        "label": "android-vr",
        "youtube": {"player_client": ["android_vr"]},
        "ua": "com.google.android.apps.youtube.vr.oculus/1.56.21 (Linux; U; Android 12; en_US; Quest 3) gzip",
    },
    {
        "label": "tv-embedded",
        "youtube": {"player_client": ["tv_embedded"], "skip": ["webpage", "configs"]},
        "ua": "Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) AppleWebKit/538.1 (KHTML, like Gecko) Version/6.0 TV Safari/538.1",
    },
]


def _extractor_args(youtube_args: dict) -> dict:
    """يفعّل bgutil PO Token provider بدون cookies."""
    youtube = deepcopy(youtube_args)
    youtube["getpot_bgutil_baseurl"] = [POT_BASE_URL]
    return {
        "youtube": youtube,
        "youtubepot-bgutilhttp": {"base_url": [POT_BASE_URL]},
    }


def _headers(ua: str) -> dict:
    h = dict(COMMON_HEADERS)
    h["User-Agent"] = ua
    return h


def _base_opts(fmt: str, outtmpl: str | None = None, download: bool = False) -> dict:
    opts = {
        "format": fmt,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "cachedir": False,
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 3,
        "socket_timeout": 20,
        "format_sort": ["res", "abr", "asr", "ext"],
    }
    if outtmpl:
        opts["outtmpl"] = outtmpl
    if not download:
        opts["skip_download"] = True
    return opts


def _audio_download_opts(outtmpl: str) -> dict:
    opts = _base_opts(AUDIO_FORMAT, outtmpl, download=True)
    opts["postprocessors"] = [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }]
    return opts


def _video_download_opts(outtmpl: str, fmt: str = VIDEO_FORMAT) -> dict:
    opts = _base_opts(fmt, outtmpl, download=True)
    opts["merge_output_format"] = "mp4"
    return opts


def _apply_strategy(opts: dict, strategy: dict) -> dict:
    opts = dict(opts)
    opts["extractor_args"] = _extractor_args(strategy["youtube"])
    opts["http_headers"] = _headers(strategy["ua"])
    return opts


def _short_error(e: Exception) -> str:
    text = str(e).replace("\n", " ").strip()
    return text[:300] or e.__class__.__name__


def _existing_file(ydl, info: dict, prefer=("mp3", "m4a", "webm", "opus", "ogg", "mp4", "mkv")) -> str | None:
    filename = ydl.prepare_filename(info)
    candidates = [filename]
    base = os.path.splitext(filename)[0]
    candidates += [f"{base}.{ext}" for ext in prefer]
    requested = info.get("requested_downloads") or []
    candidates += [item.get("filepath") for item in requested if item.get("filepath")]
    for item in dict.fromkeys(c for c in candidates if c):
        if os.path.exists(item):
            return item
    parent = Path(filename).parent
    stem = Path(base).name
    if parent.exists():
        for item in parent.glob(stem + ".*"):
            if item.is_file() and item.stat().st_size > 0:
                return str(item)
    return None


def _is_direct_url(u: str) -> bool:
    if not u:
        return False
    bad = (".mpd", "googlevideo.com/initplayback", "manifest")
    return not any(b in u for b in bad)


def _pick_url(info: dict, want_video: bool = False) -> str | None:
    url = info.get("url", "")
    if _is_direct_url(url):
        return url

    formats = list(info.get("requested_formats") or []) + list(info.get("formats") or [])
    if want_video:
        video = [
            f for f in formats
            if f.get("vcodec") != "none" and _is_direct_url(f.get("url", ""))
        ]
        if video:
            video.sort(key=lambda f: (f.get("height") or 0, f.get("tbr") or 0), reverse=True)
            return video[0]["url"]

    audio = [
        f for f in formats
        if f.get("acodec") != "none" and _is_direct_url(f.get("url", ""))
    ]
    if audio:
        audio.sort(key=lambda f: (f.get("abr") or f.get("tbr") or 0), reverse=True)
        return audio[0]["url"]
    return None


def _run_with_fallback(link: str, base_opts: dict, download: bool = False):
    last_error = "فشل YouTube بعد كل المحاولات"
    for strategy in _STRATEGIES:
        opts = _apply_strategy(base_opts, strategy)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=download)
                print(f"[ytdl_utils] OK via {strategy['label']}")
                return info, ydl, None
        except yt_dlp.utils.DownloadError as e:
            last_error = _short_error(e)
            print(f"[ytdl_utils] {strategy['label']} failed: {last_error}")
        except Exception as e:
            last_error = _short_error(e)
            print(f"[ytdl_utils] {strategy['label']} error: {last_error}")
    return None, None, last_error


def audio_opts(outtmpl: str = "/tmp/%(title).70s.%(ext)s") -> dict:
    """أول إعداد جاهز لو ملف قديم احتاج opts مباشرة."""
    return _apply_strategy(_audio_download_opts(outtmpl), _STRATEGIES[0])


def download_audio_file(link: str, outtmpl: str = "/tmp/%(title).70s.%(ext)s"):
    info, ydl, err = _run_with_fallback(link, _audio_download_opts(outtmpl), download=True)
    if not info or not ydl:
        return None, err
    filepath = _existing_file(ydl, info, prefer=("mp3", "m4a", "webm", "opus", "ogg"))
    if filepath:
        return filepath, None
    return None, "تم التحميل لكن لم يتم العثور على الملف الناتج"


def download_video_file(link: str, outtmpl: str = "/tmp/%(title).70s.%(ext)s", fmt: str = VIDEO_FORMAT):
    info, ydl, err = _run_with_fallback(link, _video_download_opts(outtmpl, fmt), download=True)
    if not info or not ydl:
        return None, None, err
    filepath = _existing_file(ydl, info, prefer=("mp4", "mkv", "webm", "mov"))
    if filepath:
        return filepath, info, None
    return None, info, "تم تحميل الفيديو لكن لم يتم العثور على الملف الناتج"


def get_audio_url(link: str):
    info, _, err = _run_with_fallback(link, _base_opts(AUDIO_FORMAT), download=False)
    if not info:
        return 0, err
    url = _pick_url(info, want_video=False)
    if url:
        return 1, url
    return 0, "فشل استخراج رابط صوت مباشر"


def get_video_url(link: str, quality: int = 720):
    fmt = f"best[height<=?{quality}][width<=?1280]/best[height<=?{quality}]/best"
    info, _, err = _run_with_fallback(link, _base_opts(fmt), download=False)
    if not info:
        return 0, err
    url = _pick_url(info, want_video=True)
    if url:
        return 1, url
    return 0, "فشل استخراج رابط فيديو مباشر"


def extract_info_no_download(link: str):
    info, _, err = _run_with_fallback(link, _base_opts("best/bestaudio/bestvideo"), download=False)
    if info:
        return info, None
    return None, err


def quality_from_format(fmt: str, default: int = 720) -> int:
    m = re.search(r"height<=[?]?(\d+)", fmt or "")
    return int(m.group(1)) if m else default
