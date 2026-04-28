# ytdl_utils.py — محرك YouTube مبسّط على نمط النسخة القديمة (World)
# الفلسفة:
#   • البحث عبر youtube-search-python (VideosSearch) — مباشر بدون APIs خارجية.
#   • استخراج رابط البث المباشر عبر `yt-dlp -g` (subprocess) — نفس طريقة النسخة القديمة.
#   • التشغيل في py-tgcalls يعتمد على رابط البث المباشر (بدون تحميل ملف).
#   • التحميل الفعلي للملفات (لـ /song و /vsong) يستخدم yt-dlp بـ player_clients غير web
#     لتقليل bot detection.
#
# الواجهات المُصدَّرة (مطلوبة من باقي ملفات البوت):
#   - extract_video_id(value) -> str | None
#   - search_youtube(query, limit=1) -> list[dict]
#   - get_video_info(url_or_id) -> dict | None
#   - get_audio_url(url_or_id) -> tuple[int, str]   # (1, stream_url) | (0, error)
#   - download_audio_file(url_or_id, outtmpl=None) -> tuple[str|None, str|None]
#   - download_video_file(url_or_id, quality=720, outtmpl=None) -> tuple[str|None, dict|None, str|None]
#   - audio_opts(outtmpl) -> dict
#   - video_opts(outtmpl, quality=720) -> dict

from __future__ import annotations

import os
import re
import shlex
import subprocess
from urllib.parse import parse_qs, urlparse

# ─────────────────────────────────────────
# إعدادات yt-dlp (player_clients غير web — نفس فكرة النسخة القديمة لكن أحدث)
# ─────────────────────────────────────────

_PLAYER_CLIENTS = ["tv_embedded", "ios", "mweb", "android"]

_COMMON_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "extractor_args": {"youtube": {"player_client": _PLAYER_CLIENTS}},
}


def audio_opts(outtmpl: str = "/tmp/%(title).70s.%(ext)s") -> dict:
    return {
        **_COMMON_OPTS,
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": outtmpl,
        "prefer_ffmpeg": True,
        "keepvideo": False,
    }


def video_opts(outtmpl: str = "/tmp/%(title).70s.%(ext)s", quality: int = 720) -> dict:
    return {
        **_COMMON_OPTS,
        "format": f"best[height<=?{quality}][width<=?1280]/best",
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
    }


# ─────────────────────────────────────────
# أدوات مساعدة
# ─────────────────────────────────────────

_VID_RE = re.compile(r"[A-Za-z0-9_-]{11}")


def extract_video_id(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    if _VID_RE.fullmatch(value):
        return value
    try:
        p = urlparse(value)
        host = p.netloc.lower()
        if "youtu.be" in host:
            vid = p.path.strip("/").split("/")[0]
            return vid if _VID_RE.fullmatch(vid or "") else None
        if "youtube.com" in host or "music.youtube.com" in host:
            qs = parse_qs(p.query)
            if qs.get("v"):
                v = qs["v"][0]
                return v if _VID_RE.fullmatch(v) else None
            m = re.search(r"/(?:shorts|embed|live|v)/([A-Za-z0-9_-]{11})", p.path)
            if m:
                return m.group(1)
    except Exception:
        pass
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/|/v/)([A-Za-z0-9_-]{11})", value)
    return m.group(1) if m else None


def _to_url(value: str) -> str:
    """يقبل ID أو رابط، ويرجع رابط YouTube قابل للاستخدام."""
    vid = extract_video_id(value)
    if vid:
        return f"https://www.youtube.com/watch?v={vid}"
    return value


def _duration_text(seconds) -> str:
    try:
        seconds = int(seconds or 0)
    except Exception:
        return "0:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# ─────────────────────────────────────────
# 1) البحث — نمط النسخة القديمة (youtube-search-python)
# ─────────────────────────────────────────

def search_youtube(query: str, limit: int = 1) -> list[dict]:
    """
    يرجع قائمة عناصر بالشكل:
      {"title", "url", "duration", "thumbnail", "id"}
    يستخدم youtubesearchpython.VideosSearch (نفس النسخة القديمة).
    وعنده fallback على youtube_search.YoutubeSearch.
    """
    query = (query or "").strip()
    if not query:
        return []

    # Primary: youtube_search.YoutubeSearch (الأكثر استقراراً مع نسخ httpx الحديثة)
    try:
        from youtube_search import YoutubeSearch
        res = YoutubeSearch(query, max_results=max(1, int(limit))).to_dict() or []
        out = []
        for r in res[:limit]:
            url_suffix = r.get("url_suffix") or ""
            url = f"https://www.youtube.com{url_suffix}" if url_suffix else ""
            vid = extract_video_id(url) or ""
            thumbs = r.get("thumbnails") or []
            thumb_url = thumbs[0] if thumbs else (f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else "")
            out.append({
                "id": vid,
                "title": r.get("title") or query,
                "url": url,
                "duration": r.get("duration") or "0:00",
                "thumbnail": thumb_url,
            })
        if out:
            return out
    except Exception as e:
        print(f"[search_youtube/YoutubeSearch] {e}")

    # Fallback: youtubesearchpython.VideosSearch (نفس النسخة القديمة)
    try:
        from youtubesearchpython import VideosSearch
        res = VideosSearch(query, limit=max(1, int(limit))).result() or {}
        items = res.get("result") or []
        out = []
        for it in items[:limit]:
            vid = it.get("id") or ""
            url = it.get("link") or (f"https://www.youtube.com/watch?v={vid}" if vid else "")
            dur = it.get("duration") or "0:00"
            thumbs = it.get("thumbnails") or []
            thumb_url = ""
            if thumbs:
                thumb_url = thumbs[0].get("url") or ""
            elif vid:
                thumb_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
            out.append({
                "id": vid,
                "title": it.get("title") or query,
                "url": url,
                "duration": dur,
                "thumbnail": thumb_url,
            })
        if out:
            return out
    except Exception as e:
        print(f"[search_youtube/VideosSearch] {e}")

    return []


# ─────────────────────────────────────────
# 2) استخراج معلومات الفيديو
# ─────────────────────────────────────────

def get_video_info(url_or_id: str) -> dict | None:
    """يرجع dict بـ {title, url, duration, thumbnail, id} أو None."""
    target = _to_url(url_or_id)
    vid = extract_video_id(target)

    # حاول yt-dlp metadata-only (سريع وبيتجاوز bot detection)
    try:
        import yt_dlp
        opts = {**_COMMON_OPTS, "skip_download": True, "format": "best"}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(target, download=False) or {}
            return {
                "id": info.get("id") or vid or "",
                "title": info.get("title") or "Unknown",
                "url": target,
                "duration": _duration_text(info.get("duration")),
                "thumbnail": info.get("thumbnail")
                or (f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else ""),
            }
    except Exception as e:
        print(f"[get_video_info/yt-dlp] {e}")

    if vid:
        return {
            "id": vid,
            "title": "YouTube Video",
            "url": target,
            "duration": "0:00",
            "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
        }
    return None


# ─────────────────────────────────────────
# 3) استخراج رابط البث المباشر (نمط `yt-dlp -g` من النسخة القديمة)
#    هذا هو القلب: بنرجع stream_url مباشرة لـ py-tgcalls بدون تحميل.
# ─────────────────────────────────────────

def _ytdlp_g(url: str, fmt: str, client: str | None = None) -> str | None:
    """ينفذ `yt-dlp -g -f <fmt>` ويرجع أول URL أو None."""
    cmd = ["yt-dlp", "-g", "--no-warnings", "--no-playlist", "-f", fmt]
    if client:
        cmd += ["--extractor-args", f"youtube:player_client={client}"]
    cmd.append(url)
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=45,
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if proc.returncode == 0 and out:
            # ياخد أول سطر (الصوت أو الفيديو الرئيسي)
            return out.splitlines()[0].strip()
        if err:
            print(f"[yt-dlp -g {client or 'default'}] {err[:200]}")
    except subprocess.TimeoutExpired:
        print(f"[yt-dlp -g {client or 'default'}] timeout")
    except FileNotFoundError:
        print("[yt-dlp -g] yt-dlp executable not found in PATH")
    except Exception as e:
        print(f"[yt-dlp -g {client or 'default'}] {e}")
    return None


def get_audio_url(url_or_id: str) -> tuple[int, str]:
    """
    يرجع رابط بث صوتي مباشر — نفس فكرة النسخة القديمة بالضبط.
    (1, stream_url) عند النجاح، (0, error_msg) عند الفشل.
    """
    target = _to_url(url_or_id)
    fmt = "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best"

    # جرّب عدة player_clients بالترتيب (الأكثر استقراراً ضد bot detection)
    last_err = ""
    for client in [None] + _PLAYER_CLIENTS:
        url = _ytdlp_g(target, fmt, client)
        if url:
            return 1, url
        last_err = client or "default"

    return 0, f"تعذر استخراج رابط الصوت (آخر محاولة: {last_err})"


def get_video_url(url_or_id: str, quality: int = 720) -> tuple[int, str]:
    """نفس get_audio_url لكن للفيديو — يرجع رابط بث فيديو مدمج."""
    target = _to_url(url_or_id)
    fmt = f"best[height<=?{quality}][width<=?1280]/best"
    last_err = ""
    for client in [None] + _PLAYER_CLIENTS:
        url = _ytdlp_g(target, fmt, client)
        if url:
            return 1, url
        last_err = client or "default"
    return 0, f"تعذر استخراج رابط الفيديو (آخر محاولة: {last_err})"


# ─────────────────────────────────────────
# 4) تحميل ملف صوتي/فيديو (لأوامر /song /vsong فقط)
#    التشغيل المباشر مش بيستخدم الدوال دي.
# ─────────────────────────────────────────

def _download_with_ydl(url: str, opts_base: dict) -> tuple[str | None, dict | None, str | None]:
    """يحاول التحميل بكل player_clients واحد تلو الآخر."""
    import yt_dlp
    last_err = None
    for client in _PLAYER_CLIENTS:
        opts = dict(opts_base)
        opts["extractor_args"] = {"youtube": {"player_client": [client]}}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    continue
                fname = ydl.prepare_filename(info)
                # لو yt-dlp غيّر الامتداد بعد التحويل
                if not os.path.exists(fname):
                    base, _ = os.path.splitext(fname)
                    for ext in (".m4a", ".webm", ".mp3", ".mp4", ".mkv"):
                        cand = base + ext
                        if os.path.exists(cand):
                            fname = cand
                            break
                if os.path.exists(fname):
                    return fname, info, None
                last_err = f"file not found after download ({client})"
        except Exception as e:
            last_err = f"{client}: {str(e)[:200]}"
            print(f"[_download_with_ydl/{client}] {e}")
            continue
    return None, None, last_err or "all player_clients failed"


def download_audio_file(url_or_id: str, outtmpl: str | None = None) -> tuple[str | None, str | None]:
    target = _to_url(url_or_id)
    opts = audio_opts(outtmpl or "/tmp/%(title).70s.%(ext)s")
    fname, _info, err = _download_with_ydl(target, opts)
    return fname, err


def download_video_file(
    url_or_id: str, quality: int = 720, outtmpl: str | None = None
) -> tuple[str | None, dict | None, str | None]:
    target = _to_url(url_or_id)
    opts = video_opts(outtmpl or "/tmp/%(title).70s.%(ext)s", quality=quality)
    return _download_with_ydl(target, opts)
