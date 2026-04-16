import asyncio
import os
import yt_dlp
from program.ytsearch_core import ytsearch, ytsearch_async

AUDIO_DIR = "/tmp/tgbot_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")

def _cookies_opt() -> dict:
    if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
        return {"cookiefile": COOKIES_FILE}
    return {}

# ✅ format مرن يقبل أي صيغة صوتية
_AUDIO_FMT = (
    "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio[ext=opus]"
    "/bestaudio/best[acodec!=none]/best/bestaudio*"
)

_STRATEGIES = [
    {
        "label": "tv_embedded",
        "extractor_args": {"youtube": {"player_client": ["tv_embedded"], "skip": ["webpage"]}},
        "http_headers": {"User-Agent": "Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) AppleWebKit/538.1 (KHTML, like Gecko) Version/6.0 TV Safari/538.1"},
    },
    {
        "label": "ios",
        "extractor_args": {"youtube": {"player_client": ["ios"]}},
        "http_headers": {"User-Agent": "com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)"},
    },
    {
        "label": "android",
        "extractor_args": {"youtube": {"player_client": ["android"]}},
        "http_headers": {"User-Agent": "com.google.android.youtube/19.29.37 (Linux; U; Android 14; en_US; Pixel 8; Build/UQ1A.240605.004;) gzip"},
    },
    {
        "label": "web_creator",
        "extractor_args": {"youtube": {"player_client": ["web_creator"]}},
        "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"},
    },
    {
        "label": "mweb",
        "extractor_args": {"youtube": {"player_client": ["mweb"]}},
        "http_headers": {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"},
    },
]


def _is_direct_url(u: str) -> bool:
    if not u:
        return False
    bad = (".mpd", ".m3u8", "googlevideo.com/initplayback", "manifest")
    return not any(b in u for b in bad)


async def ytdl_audio(link: str):
    """استخراج رابط الصوت المباشر مع fallback متعدد المحاولات"""
    def _get():
        for s in _STRATEGIES:
            ydl_opts = {
                "format": _AUDIO_FMT,
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "skip_download": True,
                "format_sort": ["abr", "asr", "ext"],
                "extractor_args": s["extractor_args"],
                "http_headers": s["http_headers"],
            }
            ydl_opts.update(_cookies_opt())
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=False)

                    url = info.get("url")
                    if _is_direct_url(url):
                        print(f"[ytdl_audio] OK via {s['label']}")
                        return 1, url

                    for rf in (info.get("requested_formats") or []):
                        u = rf.get("url", "")
                        if _is_direct_url(u):
                            print(f"[ytdl_audio] OK via {s['label']} (requested_formats)")
                            return 1, u

                    formats = info.get("formats") or []
                    audio_only = [f for f in formats if f.get("vcodec") == "none" and _is_direct_url(f.get("url", ""))]
                    if audio_only:
                        audio_only.sort(key=lambda f: f.get("abr") or f.get("tbr") or 0, reverse=True)
                        print(f"[ytdl_audio] OK via {s['label']} (audio_only)")
                        return 1, audio_only[0]["url"]

                    for f in reversed(formats):
                        u = f.get("url", "")
                        if _is_direct_url(u):
                            print(f"[ytdl_audio] OK via {s['label']} (fallback format)")
                            return 1, u

            except Exception as e:
                print(f"[ytdl_audio] {s['label']} failed: {str(e)[:120]}")

        return 0, "فشل استخراج رابط الصوت — جميع المحاولات فشلت"

    return await asyncio.to_thread(_get)
