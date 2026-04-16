# ytdl_utils.py — مركزي لإعدادات yt_dlp مع fallback لإصلاح "Requested format is not available"
# ✅ الإصلاح النهائي: format مرن + player clients محدّثة + دعم cookies

import os
import yt_dlp

# ─────────────────────────────────────────
# الفورمات المرنة — تقبل أي صيغة صوتية متاحة
# ─────────────────────────────────────────

AUDIO_FORMAT = (
    "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio[ext=opus]"
    "/bestaudio/best[acodec!=none]/best/bestaudio*"
)

# ─────────────────────────────────────────
# Player clients بالترتيب — الأسرع والأكثر نجاحاً أول
# ─────────────────────────────────────────

_STRATEGIES = [
    {
        "label": "web_creator",
        "extractor_args": {
            "youtube": {"player_client": ["web_creator"]}
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    },
    {
        "label": "tv_embedded",
        "extractor_args": {
            "youtube": {
                "player_client": ["tv_embedded"],
                "skip": ["webpage"],
            }
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) "
                "AppleWebKit/538.1 (KHTML, like Gecko) Version/6.0 TV Safari/538.1"
            )
        },
    },
    {
        "label": "ios",
        "extractor_args": {
            "youtube": {"player_client": ["ios"]}
        },
        "http_headers": {
            "User-Agent": (
                "com.google.ios.youtube/19.29.1 "
                "(iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)"
            )
        },
    },
    {
        "label": "android",
        "extractor_args": {
            "youtube": {"player_client": ["android"]}
        },
        "http_headers": {
            "User-Agent": (
                "com.google.android.youtube/19.29.37 "
                "(Linux; U; Android 14; en_US; Pixel 8; Build/UQ1A.240605.004;) gzip"
            )
        },
    },
    {
        "label": "mweb",
        "extractor_args": {
            "youtube": {"player_client": ["mweb"]}
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 10; K) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Mobile Safari/537.36"
            )
        },
    },
]


def _get_cookies_path():
    return os.path.join(os.path.dirname(__file__), "cookies.txt")


def _base_opts(outtmpl: str, fmt: str) -> dict:
    opts = {
        "format": fmt,
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "format_sort": ["abr", "asr", "ext"],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    cookies_file = _get_cookies_path()
    if os.path.isfile(cookies_file):
        opts["cookiefile"] = cookies_file
    return opts


def _base_info_opts(fmt: str) -> dict:
    opts = {
        "format": fmt,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "skip_download": True,
        "format_sort": ["abr", "asr", "ext"],
    }
    cookies_file = _get_cookies_path()
    if os.path.isfile(cookies_file):
        opts["cookiefile"] = cookies_file
    return opts


def audio_opts(outtmpl: str = "/tmp/%(title)s.%(ext)s") -> dict:
    opts = _base_opts(outtmpl, AUDIO_FORMAT)
    opts["extractor_args"] = _STRATEGIES[0]["extractor_args"]
    opts["http_headers"] = _STRATEGIES[0]["http_headers"]
    return opts


def download_audio_file(link: str, outtmpl: str = "/tmp/%(title)s.%(ext)s"):
    """
    يحمّل الصوت من الرابط مع fallback تلقائي بين player clients.
    يرجع: (filepath, None) لو نجح، أو (None, error_msg) لو فشل.
    """
    last_error = "فشل التحميل — كل الـ strategies فشلت"

    for strategy in _STRATEGIES:
        opts = _base_opts(outtmpl, AUDIO_FORMAT)
        opts["extractor_args"] = strategy["extractor_args"]
        if strategy["http_headers"]:
            opts["http_headers"] = strategy["http_headers"]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                filepath = ydl.prepare_filename(info)

                if not os.path.exists(filepath):
                    base = os.path.splitext(filepath)[0]
                    for ext in ("mp3", "m4a", "webm", "opus", "ogg"):
                        candidate = f"{base}.{ext}"
                        if os.path.exists(candidate):
                            filepath = candidate
                            break

                if os.path.exists(filepath):
                    print(f"[ytdl_utils] ✅ نجح عبر {strategy['label']}: {filepath}")
                    return filepath, None

        except yt_dlp.utils.DownloadError as e:
            last_error = str(e)[:200]
            print(f"[ytdl_utils] ❌ {strategy['label']} فشل: {last_error}")
            continue
        except Exception as e:
            last_error = str(e)[:200]
            print(f"[ytdl_utils] ❌ {strategy['label']} خطأ: {last_error}")
            continue

    return None, last_error


def get_audio_url(link: str):
    """يرجع (1, stream_url) أو (0, error_msg)."""
    last_error = "فشل الحصول على الرابط"

    for strategy in _STRATEGIES:
        opts = _base_info_opts(AUDIO_FORMAT)
        opts["extractor_args"] = strategy["extractor_args"]
        if strategy["http_headers"]:
            opts["http_headers"] = strategy["http_headers"]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=False)

                url = info.get("url", "")
                if _is_direct_url(url):
                    print(f"[ytdl_utils] ✅ URL عبر {strategy['label']}")
                    return 1, url

                for rf in (info.get("requested_formats") or []):
                    u = rf.get("url", "")
                    if _is_direct_url(u):
                        return 1, u

                formats = info.get("formats") or []
                audio_only = [
                    f for f in formats
                    if f.get("vcodec") == "none" and _is_direct_url(f.get("url", ""))
                ]
                if audio_only:
                    audio_only.sort(key=lambda f: f.get("abr") or f.get("tbr") or 0, reverse=True)
                    return 1, audio_only[0]["url"]

                all_formats = [f for f in formats if _is_direct_url(f.get("url", ""))]
                if all_formats:
                    return 1, all_formats[-1]["url"]

        except Exception as e:
            last_error = str(e)[:200]
            print(f"[ytdl_utils] ❌ get_url/{strategy['label']}: {last_error}")
            continue

    return 0, last_error


def _is_direct_url(u: str) -> bool:
    if not u:
        return False
    bad = (".mpd", ".m3u8", "googlevideo.com/initplayback", "manifest")
    return not any(b in u for b in bad)
