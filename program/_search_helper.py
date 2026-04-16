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


async def ytdl_audio(link: str):
    """استخراج رابط الصوت المباشر مع fallback متعدد المحاولات"""
    def _get():
        # ترتيب العملاء: tv_embedded الأقل تقييداً أولاً
        # لا تضع skip: ["hls","dash"] — هؤلاء العملاء بيخدموا HLS فقط!
        strategies = [
            {
                "label": "tv_embedded",
                "extractor_args": {"youtube": {"player_client": ["tv_embedded"]}},
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
                "label": "web",
                "extractor_args": {"youtube": {"player_client": ["web"]}},
                "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"},
            },
        ]

        for s in strategies:
            ydl_opts = {
                "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "skip_download": True,
                "extractor_args": s["extractor_args"],
                "http_headers": s["http_headers"],
            }
            ydl_opts.update(_cookies_opt())
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    # جرب url مباشر
                    url = info.get("url")
                    # لو مفيش، جرب requested_formats
                    if not url and info.get("requested_formats"):
                        url = info["requested_formats"][0].get("url")
                    # لو مفيش، جرب formats
                    if not url:
                        for f in reversed(info.get("formats") or []):
                            u = f.get("url", "")
                            if u and not u.startswith("manifest"):
                                url = u
                                break
                    if url:
                        print(f"[ytdl_audio] OK via {s['label']}")
                        return 1, url
            except Exception as e:
                print(f"[ytdl_audio] {s['label']} failed: {str(e)[:120]}")

        return 0, "فشل استخراج رابط الصوت — جميع المحاولات فشلت"

    return await asyncio.to_thread(_get)
