# ytdl_utils.py — إعدادات yt-dlp المركزية
# لتجديد الكوكيز: استبدل ملف cookies.txt بس — مش محتاج تعدل أي حاجة تانية

import os

# مسار ملف الكوكيز — موجود في root المشروع
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

# ─────────────────────────────────────────
# helpers داخلية
# ─────────────────────────────────────────

def _is_bgutil_running() -> bool:
    """تحقق إذا bgutil server شغال على port 4416"""
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:4416/get_visitor_data", timeout=2)
        return True
    except Exception:
        return False


def _extractor_args(use_pot: bool = False) -> dict:
    if use_pot and _is_bgutil_running():
        return {
            "youtube": {
                "player_client": ["web"],
                "po_token": ["web+http://localhost:4416/get_po_token"],
                "visitor_data": ["http://localhost:4416/get_visitor_data"],
            }
        }
    # tv_embedded + ios بيرجعوا streams مباشرة بدون DASH/HLS manifest
    return {
        "youtube": {
            "player_client": ["tv_embedded", "ios", "web"],
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
    """Options لتحميل أفضل صوت — مع fallback تلقائي"""
    use_pot = _is_bgutil_running()
    opts = {
        # bestaudio[ext=m4a] أو webm أو أي صوت، ثم best كـ fallback نهائي
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": out_tpl,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": _extractor_args(use_pot=use_pot),
        "http_headers": _http_headers(),
    }
    opts.update(_cookies_opt())
    return opts


def video_opts(out_tpl: str = "/tmp/%(title)s.%(ext)s", height: int = 720) -> dict:
    """Options لتحميل أفضل فيديو — مع fallback تلقائي"""
    use_pot = _is_bgutil_running()
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
        "extractor_args": _extractor_args(use_pot=use_pot),
        "http_headers": _http_headers(),
    }
    opts.update(_cookies_opt())
    return opts


def stream_opts(fmt: str = "bestaudio[ext=m4a]/bestaudio/best") -> dict:
    """Options لاستخراج رابط مباشر بدون تحميل"""
    use_pot = _is_bgutil_running()
    opts = {
        "format": fmt,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extractor_args": _extractor_args(use_pot=use_pot),
        "http_headers": _http_headers(),
    }
    opts.update(_cookies_opt())
    return opts


# ─────────────────────────────────────────
# تحميل الأغنية كملف مؤقت (الحل الموثوق)
# ─────────────────────────────────────────

_DOWNLOAD_STRATEGIES = [
    {"extractor_args": {"youtube": {"player_client": ["tv_embedded", "ios"]}}},
    {"extractor_args": {"youtube": {"player_client": ["ios"]}},
     "http_headers": {"User-Agent": "com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)"}},
    {"extractor_args": {"youtube": {"player_client": ["android"]}},
     "http_headers": {"User-Agent": "com.google.android.youtube/19.29.37 (Linux; U; Android 14) gzip"}},
    {"extractor_args": {"youtube": {"player_client": ["web_creator"]}}},
    {},  # fallback بدون أي player_client
]

def download_audio_file(link: str, out_tpl: str = "/tmp/%(id)s.%(ext)s") -> tuple:
    """
    يحمّل الأغنية كملف مؤقت ويرجع (filepath, error_msg).
    يجرب استراتيجيات متعددة تلقائياً لو فشل format معين.
    """
    import yt_dlp as _yt

    base = {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": out_tpl,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "http_headers": _http_headers(),
    }
    base.update(_cookies_opt())

    last_err = "فشل التحميل"
    for strategy in _DOWNLOAD_STRATEGIES:
        opts = {**base, **strategy}
        try:
            with _yt.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                path = ydl.prepare_filename(info)
                if os.path.exists(path):
                    return path, None
                # بعض الأحيان بيتغير الامتداد بعد postprocessing
                import glob
                vid_id = info.get("id", "")
                matches = glob.glob(f"/tmp/{vid_id}.*") if vid_id else []
                if matches:
                    return matches[0], None
        except Exception as e:
            last_err = str(e)
            print(f"[download_audio_file] strategy failed: {last_err[:100]}")

    return None, last_err
