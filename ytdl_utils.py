# ytdl_utils.py — إعدادات yt-dlp المركزية
# لتجديد الكوكيز: استبدل ملف cookies.txt بس — مش محتاج تعدل أي حاجة تانية

import os

# مسار ملف الكوكيز — موجود في root المشروع
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

# ─────────────────────────────────────────
# helpers داخلية
# ─────────────────────────────────────────

def _extractor_args() -> dict:
    # ملاحظة مهمة: لا تضف skip: ["hls", "dash"]
    # tv_embedded و mweb و ios كلهم بيرجعوا HLS/DASH فقط —
    # لو حذفتهم مش هيلاقي أي فورمات!
    return {
        "youtube": {
            "player_client": ["tv_embedded", "web", "mweb", "ios"],
        }
    }


def _http_headers() -> dict:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 10; K) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Mobile Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }


def _cookies_opt() -> dict:
    """يرجع cookiefile بس لو الملف موجود فعلاً وغير فاضي"""
    if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
        return {"cookiefile": COOKIES_FILE}
    return {}


# ─────────────────────────────────────────
# الـ yt-dlp options الجاهزة
# ─────────────────────────────────────────

def audio_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s") -> dict:
    """Options لتحميل أفضل صوت"""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": out_tpl,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": _extractor_args(),
        "http_headers": _http_headers(),
    }
    opts.update(_cookies_opt())
    return opts


def video_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s", height: int = 720) -> dict:
    """Options لتحميل أفضل فيديو"""
    opts = {
        "format": (
            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={height}]+bestaudio"
            f"/best[height<={height}]"
            f"/best"
        ),
        "outtmpl": out_tpl,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
        "extractor_args": _extractor_args(),
        "http_headers": _http_headers(),
    }
    opts.update(_cookies_opt())
    return opts


def stream_opts(fmt: str = "bestaudio/best") -> dict:
    """Options لاستخراج رابط مباشر بدون تحميل"""
    opts = {
        "format": fmt,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extractor_args": _extractor_args(),
        "http_headers": _http_headers(),
    }
    opts.update(_cookies_opt())
    return opts
