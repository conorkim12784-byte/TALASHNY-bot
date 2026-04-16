# ytdl_utils.py — مركزي لإعدادات yt_dlp مع fallback لإصلاح "Requested format is not available"

import os
import yt_dlp

# ─────────────────────────────────────────
# الفورمات الصحيحة — واسعة بحيث تشتغل دايماً
# ─────────────────────────────────────────

# صوت فقط: يجرب أفضل صوت، وإلا ياخد best كاملة
AUDIO_FORMAT = (
    "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio[ext=opus]"
    "/bestaudio/best[acodec!=none]/best"
)

# ─────────────────────────────────────────
# Player clients بالترتيب (fallback chain)
# ─────────────────────────────────────────

_STRATEGIES = [
    {
        "label": "ios",
        "extractor_args": {"youtube": {"player_client": ["ios"]}},
        "http_headers": {
            "User-Agent": (
                "com.google.ios.youtube/19.29.1 "
                "(iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)"
            )
        },
    },
    {
        "label": "android",
        "extractor_args": {"youtube": {"player_client": ["android"]}},
        "http_headers": {
            "User-Agent": (
                "com.google.android.youtube/19.29.37 "
                "(Linux; U; Android 14; en_US; Pixel 8; Build/UQ1A.240605.004;) gzip"
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
        "label": "web_creator",
        "extractor_args": {"youtube": {"player_client": ["web_creator"]}},
        "http_headers": {},
    },
    {
        "label": "mweb",
        "extractor_args": {"youtube": {"player_client": ["mweb"]}},
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 10; K) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            )
        },
    },
]


def _base_opts(outtmpl: str, fmt: str) -> dict:
    """إعدادات أساسية مشتركة"""
    opts = {
        "format": fmt,
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    # أضف cookies لو موجودة
    cookies_file = os.path.join(os.path.dirname(__file__), "cookies.txt")
    if os.path.isfile(cookies_file):
        opts["cookiefile"] = cookies_file
    return opts


# ─────────────────────────────────────────
# audio_opts — للاستخدام في downloader.py
# يرجع dict جاهز مع أفضل strategy
# ─────────────────────────────────────────

def audio_opts(outtmpl: str = "/tmp/%(title)s.%(ext)s") -> dict:
    """
    يرجع dict إعدادات yt_dlp للصوت.
    يستخدم ios كـ default strategy (الأفضل حالياً).
    """
    opts = _base_opts(outtmpl, AUDIO_FORMAT)
    opts["extractor_args"] = _STRATEGIES[0]["extractor_args"]
    opts["http_headers"] = _STRATEGIES[0]["http_headers"]
    return opts


# ─────────────────────────────────────────
# download_audio_file — للاستخدام في play_engine.py
# يحمّل الملف ويرجع (filepath, None) أو (None, error)
# ─────────────────────────────────────────

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

                # لو الملف اتحول لـ mp3 بعد الـ postprocessor
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


# ─────────────────────────────────────────
# get_audio_url — يرجع رابط stream مباشر (بدون تحميل)
# ─────────────────────────────────────────

def get_audio_url(link: str):
    """
    يرجع (1, stream_url) أو (0, error_msg).
    مفيد للـ voice chat streaming بدون تحميل ملف.
    """
    last_error = "فشل الحصول على الرابط"

    for strategy in _STRATEGIES:
        opts = {
            "format": AUDIO_FORMAT,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "skip_download": True,
            "extractor_args": strategy["extractor_args"],
        }
        if strategy["http_headers"]:
            opts["http_headers"] = strategy["http_headers"]

        cookies_file = os.path.join(os.path.dirname(__file__), "cookies.txt")
        if os.path.isfile(cookies_file):
            opts["cookiefile"] = cookies_file

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=False)

                # ابحث عن URL مباشر (مش manifest)
                url = info.get("url", "")
                if _is_direct_url(url):
                    print(f"[ytdl_utils] ✅ URL عبر {strategy['label']}")
                    return 1, url

                # جرب requested_formats
                for rf in (info.get("requested_formats") or []):
                    u = rf.get("url", "")
                    if _is_direct_url(u):
                        return 1, u

                # جرب formats قائمة كاملة
                formats = info.get("formats") or []
                audio_only = [
                    f for f in formats
                    if f.get("vcodec") == "none" and _is_direct_url(f.get("url", ""))
                ]
                if audio_only:
                    audio_only.sort(key=lambda f: f.get("abr") or f.get("tbr") or 0, reverse=True)
                    return 1, audio_only[0]["url"]

        except Exception as e:
            last_error = str(e)[:200]
            print(f"[ytdl_utils] ❌ get_url/{strategy['label']}: {last_error}")
            continue

    return 0, last_error


def _is_direct_url(u: str) -> bool:
    """True لو الـ URL مباشر (مش manifest أو mpd)"""
    if not u:
        return False
    bad = (".mpd", ".m3u8", "googlevideo.com/initplayback", "manifest")
    return not any(b in u for b in bad)
