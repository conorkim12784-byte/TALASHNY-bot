import os

COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

def _is_bgutil_running() -> bool:
    # تعطيل bgutil بالكامل لتجنب مشاكل canvas
    return False

def _extractor_args(use_pot: bool = False) -> dict:
    # استخدام clients آمنة بدون POT
    return {
        "youtube": {
            "player_client": ["android", "web"],
        }
    }

def _http_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0",
    }

def _cookies_opt() -> dict:
    if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
        return {"cookiefile": COOKIES_FILE}
    return {}

def audio_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s") -> dict:
    opts = {
        "format": "bestaudio/best",
        "outtmpl": out_tpl,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "extractor_args": _extractor_args(),
        "http_headers": _http_headers(),
    }
    opts.update(_cookies_opt())
    return opts

def video_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s", height: int = 720) -> dict:
    opts = {
        "format": "best",
        "outtmpl": out_tpl,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "merge_output_format": "mp4",
        "extractor_args": _extractor_args(),
        "http_headers": _http_headers(),
    }
    opts.update(_cookies_opt())
    return opts

def stream_opts(fmt: str = "bestaudio/best") -> dict:
    opts = {
        "format": fmt,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "nocheckcertificate": True,
        "extractor_args": _extractor_args(),
        "http_headers": _http_headers(),
    }
    opts.update(_cookies_opt())
    return opts
