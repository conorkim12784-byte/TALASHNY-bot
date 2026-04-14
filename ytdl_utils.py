# ytdl_utils.py — إعدادات yt-dlp المركزية
# لتجديد الكوكيز: استبدل ملف cookies.txt بس — مش محتاج تعدل أي حاجة تانية

import os

# مسار ملف الكوكيز — موجود في root المشروع
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

# ─────────────────────────────────────────
# الـ yt-dlp options الجاهزة
# ─────────────────────────────────────────

def audio_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s") -> dict:
    """Options لتحميل أفضل صوت"""
    return {
        "format": "bestaudio/best",
        "outtmpl": out_tpl,
        "cookiefile": COOKIES_FILE,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        # mweb هو الأنجح في 2025 عشان YouTube مش بيبلوكه
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "ios", "tv_embedded", "web"],
                "skip": ["hls", "dash"],
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }


def video_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s", height: int = 720) -> dict:
    """Options لتحميل أفضل فيديو"""
    return {
        "format": f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
        "outtmpl": out_tpl,
        "cookiefile": COOKIES_FILE,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "ios", "tv_embedded", "web"],
                "skip": ["hls", "dash"],
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }


def stream_opts(fmt: str = "bestaudio/best") -> dict:
    """Options لاستخراج رابط مباشر بدون تحميل"""
    return {
        "format": fmt,
        "cookiefile": COOKIES_FILE,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "ios", "tv_embedded", "web"],
                "skip": ["hls", "dash"],
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
