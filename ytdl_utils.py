# ytdl_utils.py — محرك YouTube جديد بدون cookies
# الأولوية: Piped API / Invidious-like public endpoints لاستخراج البحث والروابط المباشرة
# الاحتياطي الأخير فقط: yt-dlp بعملاء غير web لتقليل أخطاء bot detection

import os
import re
import time
import uuid
import shutil
import subprocess
from urllib.parse import parse_qs, urlparse

import requests
import yt_dlp

AUDIO_FORMAT = "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best"

PIPED_INSTANCES = [
    "https://api.piped.private.coffee",
    "https://pipedapi.adminforge.de",
    "https://api.piped.yt",
    "https://pipedapi.privacy.com.de",
    "https://pipedapi.kavin.rocks",
    "https://pipedapi-libre.kavin.rocks",
]

_REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
}

_YTDLP_STRATEGIES = [
    {
        "label": "tv_embedded",
        "extractor_args": {"youtube": {"player_client": ["tv_embedded"], "skip": ["webpage", "configs"]}},
        "http_headers": {"User-Agent": "Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) AppleWebKit/538.1 Version/6.0 TV Safari/538.1"},
    },
    {
        "label": "mweb",
        "extractor_args": {"youtube": {"player_client": ["mweb"]}},
        "http_headers": {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"},
    },
    {
        "label": "ios",
        "extractor_args": {"youtube": {"player_client": ["ios"]}},
        "http_headers": {"User-Agent": "com.google.ios.youtube/19.45.4 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)"},
    },
]


def _duration_text(seconds) -> str:
    try:
        seconds = int(seconds or 0)
    except Exception:
        return "0:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def extract_video_id(value: str) -> str | None:
    value = (value or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    try:
        p = urlparse(value)
        host = p.netloc.lower()
        if "youtu.be" in host:
            vid = p.path.strip("/").split("/")[0]
            return vid if re.fullmatch(r"[A-Za-z0-9_-]{11}", vid or "") else None
        if "youtube.com" in host:
            qs = parse_qs(p.query)
            if qs.get("v"):
                return qs["v"][0]
            m = re.search(r"/(?:shorts|embed|live)/([A-Za-z0-9_-]{11})", p.path)
            if m:
                return m.group(1)
    except Exception:
        pass
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})", value)
    return m.group(1) if m else None


def _clean_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("/watch?v="):
        return "https://www.youtube.com" + url
    return url


def _video_id_from_item_url(url: str) -> str | None:
    return extract_video_id(_clean_url(url))


def _piped_request(path: str, params=None, timeout=10):
    last = None
    for base in PIPED_INSTANCES:
        try:
            endpoint = f"{base.rstrip('/')}/{path.lstrip('/')}"
            r = requests.get(endpoint, params=params or {}, headers=_REQ_HEADERS, timeout=timeout)
            if r.status_code == 200 and r.text.strip():
                return base, r.json()
            last = f"{base}: HTTP {r.status_code}"
        except Exception as e:
            last = f"{base}: {str(e)[:120]}"
            continue
    raise RuntimeError(last or "كل سيرفرات Piped فشلت")


def search_youtube(query: str, limit: int = 1) -> list:
    """بحث YouTube عبر Piped API بدل scraping مباشر من youtube.com."""
    try:
        _, data = _piped_request("/search", {"q": query, "filter": "videos"}, timeout=10)
        items = data.get("items", data) if isinstance(data, dict) else data
        results = []
        for item in items or []:
            if item.get("type") not in (None, "stream"):
                continue
            vid = _video_id_from_item_url(item.get("url", ""))
            title = item.get("title") or query
            if not vid or not title:
                continue
            results.append({
                "id": vid,
                "title": title[:70],
                "url": f"https://www.youtube.com/watch?v={vid}",
                "duration": _duration_text(item.get("duration")),
                "duration_seconds": int(item.get("duration") or 0),
                "thumbnail": item.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "channel": item.get("uploaderName", ""),
                "views": str(item.get("views", "")),
            })
            if len(results) >= limit:
                break
        return results
    except Exception as e:
        print(f"[piped search] failed: {e}")
        return _yt_dlp_search(query, limit)


def _yt_dlp_search(query: str, limit: int = 1) -> list:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": "in_playlist", "nocheckcertificate": True}
    for s in _YTDLP_STRATEGIES:
        try:
            o = dict(opts)
            o.update({"extractor_args": s["extractor_args"], "http_headers": s["http_headers"]})
            with yt_dlp.YoutubeDL(o) as ydl:
                data = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            out = []
            for e in data.get("entries", []) or []:
                vid = e.get("id") or extract_video_id(e.get("url", ""))
                if not vid:
                    continue
                out.append({
                    "id": vid,
                    "title": (e.get("title") or query)[:70],
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "duration": _duration_text(e.get("duration")),
                    "duration_seconds": int(e.get("duration") or 0),
                    "thumbnail": e.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                    "channel": e.get("uploader") or "",
                    "views": "",
                })
            if out:
                return out[:limit]
        except Exception as e:
            print(f"[yt-dlp search/{s['label']}] {str(e)[:120]}")
    return []


def get_video_info(link_or_id: str) -> dict | None:
    vid = extract_video_id(link_or_id)
    if not vid:
        return None
    try:
        _, data = _piped_request(f"/streams/{vid}", timeout=10)
        title = data.get("title") or "YouTube Audio"
        return {
            "id": vid,
            "title": title[:70],
            "url": f"https://www.youtube.com/watch?v={vid}",
            "duration": _duration_text(data.get("duration")),
            "duration_seconds": int(data.get("duration") or 0),
            "thumbnail": data.get("thumbnailUrl") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            "raw": data,
        }
    except Exception as e:
        print(f"[piped info] failed: {e}")
        return _yt_dlp_info(vid)


def _yt_dlp_info(vid: str) -> dict | None:
    link = f"https://www.youtube.com/watch?v={vid}"
    for s in _YTDLP_STRATEGIES:
        try:
            opts = {"quiet": True, "no_warnings": True, "skip_download": True, "nocheckcertificate": True,
                    "extractor_args": s["extractor_args"], "http_headers": s["http_headers"]}
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(link, download=False)
            return {
                "id": vid,
                "title": (data.get("title") or "YouTube Audio")[:70],
                "url": link,
                "duration": _duration_text(data.get("duration")),
                "duration_seconds": int(data.get("duration") or 0),
                "thumbnail": data.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "raw": data,
            }
        except Exception as e:
            print(f"[yt-dlp info/{s['label']}] {str(e)[:120]}")
    return None


def _pick_audio_stream(streams: list) -> dict | None:
    if not streams:
        return None
    def score(x):
        return int(x.get("bitrate") or x.get("quality") or x.get("abr") or 0)
    return sorted(streams, key=score, reverse=True)[0]


def _pick_video_stream(streams: list, quality=720) -> dict | None:
    if not streams:
        return None
    def height(x):
        q = str(x.get("quality") or x.get("qualityLabel") or "")
        m = re.search(r"(\d{3,4})", q)
        return int(x.get("height") or (m.group(1) if m else 0) or 0)
    filtered = [s for s in streams if height(s) and height(s) <= int(quality or 720)] or streams
    return sorted(filtered, key=height, reverse=True)[0]


def _is_direct_url(u: str) -> bool:
    return bool(u and u.startswith("http") and ".m3u8" not in u and ".mpd" not in u)


def get_audio_url(link: str):
    """يرجع (1, direct_audio_url) أو (0, error)."""
    vid = extract_video_id(link)
    if not vid:
        return 0, "رابط YouTube غير صالح"
    try:
        _, data = _piped_request(f"/streams/{vid}", timeout=10)
        s = _pick_audio_stream(data.get("audioStreams") or [])
        if s and _is_direct_url(s.get("url")):
            print("[audio] OK via Piped")
            return 1, s["url"]
    except Exception as e:
        print(f"[audio Piped] failed: {e}")
    return _yt_dlp_audio_url(f"https://www.youtube.com/watch?v={vid}")


def get_video_url(link: str, quality=720):
    """يرجع رابط فيديو مباشر. لو الصوت والفيديو منفصلين بيرجع الأفضل المتاح؛ للتحميل استخدم download_video_file."""
    vid = extract_video_id(link)
    if not vid:
        return 0, "رابط YouTube غير صالح"
    try:
        _, data = _piped_request(f"/streams/{vid}", timeout=10)
        progressive = [s for s in (data.get("videoStreams") or []) if s.get("audioTrackId") or s.get("hasAudio")]
        s = _pick_video_stream(progressive or data.get("videoStreams") or [], quality)
        if s and _is_direct_url(s.get("url")):
            print("[video] OK via Piped")
            return 1, s["url"]
    except Exception as e:
        print(f"[video Piped] failed: {e}")
    return _yt_dlp_video_url(f"https://www.youtube.com/watch?v={vid}", quality)


def _pick_url_from_ytdlp(info: dict, audio=True):
    url = info.get("url")
    if _is_direct_url(url):
        return url
    formats = info.get("formats") or []
    if audio:
        choices = [f for f in formats if f.get("vcodec") == "none" and _is_direct_url(f.get("url", ""))]
        choices.sort(key=lambda f: f.get("abr") or f.get("tbr") or 0, reverse=True)
    else:
        choices = [f for f in formats if _is_direct_url(f.get("url", ""))]
        choices.sort(key=lambda f: (f.get("height") or 0, f.get("tbr") or 0), reverse=True)
    return choices[0]["url"] if choices else None


def _yt_dlp_audio_url(link: str):
    last = "فشل استخراج رابط الصوت"
    for s in _YTDLP_STRATEGIES:
        try:
            opts = {"format": AUDIO_FORMAT, "quiet": True, "no_warnings": True, "skip_download": True,
                    "nocheckcertificate": True, "cachedir": False, "extractor_args": s["extractor_args"],
                    "http_headers": s["http_headers"]}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=False)
            url = _pick_url_from_ytdlp(info, audio=True)
            if url:
                print(f"[audio] OK via yt-dlp/{s['label']}")
                return 1, url
        except Exception as e:
            last = str(e)[:250]
    return 0, last


def _yt_dlp_video_url(link: str, quality=720):
    last = "فشل استخراج رابط الفيديو"
    fmt = f"best[height<=?{quality}]/best"
    for s in _YTDLP_STRATEGIES:
        try:
            opts = {"format": fmt, "quiet": True, "no_warnings": True, "skip_download": True,
                    "nocheckcertificate": True, "cachedir": False, "extractor_args": s["extractor_args"],
                    "http_headers": s["http_headers"]}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=False)
            url = _pick_url_from_ytdlp(info, audio=False)
            if url:
                print(f"[video] OK via yt-dlp/{s['label']}")
                return 1, url
        except Exception as e:
            last = str(e)[:250]
    return 0, last


def _safe_name(name: str) -> str:
    name = re.sub(r"[^\w\-.\u0600-\u06FF ]+", "_", (name or "audio")).strip()[:60]
    return name or str(uuid.uuid4())


def _run_ffmpeg(args: list, timeout=600):
    if not shutil.which("ffmpeg"):
        return False, "ffmpeg غير مثبت"
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    if p.returncode == 0:
        return True, None
    return False, (p.stderr or p.stdout or "ffmpeg failed")[-500:]


def download_audio_file(link: str, outtmpl: str = "/tmp/%(title).70s.%(ext)s"):
    """يحمل الصوت MP3 من Piped أولاً بدون cookies."""
    info = get_video_info(link) or {"title": "YouTube Audio"}
    ok, audio = get_audio_url(link)
    if ok == 0:
        return None, audio
    out = os.path.join("/tmp", f"{_safe_name(info.get('title'))}-{int(time.time())}.mp3")
    cmd = ["ffmpeg", "-y", "-nostdin", "-headers", f"User-Agent: {_REQ_HEADERS['User-Agent']}\r\n", "-i", audio,
           "-vn", "-acodec", "libmp3lame", "-b:a", "192k", out]
    success, err = _run_ffmpeg(cmd)
    if success and os.path.exists(out) and os.path.getsize(out) > 0:
        return out, None
    return None, err or "فشل تحميل الصوت"


def download_video_file(link: str, quality=720):
    """يحمل فيديو MP4 بالصوت من Piped؛ يرجع (file, info, err)."""
    info = get_video_info(link) or {"title": "YouTube Video", "duration_seconds": 0}
    vid = extract_video_id(link)
    try:
        _, data = _piped_request(f"/streams/{vid}", timeout=10)
        audio_s = _pick_audio_stream(data.get("audioStreams") or [])
        video_s = _pick_video_stream(data.get("videoStreams") or [], quality)
        if audio_s and video_s and audio_s.get("url") and video_s.get("url"):
            out = os.path.join("/tmp", f"{_safe_name(info.get('title'))}-{int(time.time())}.mp4")
            cmd = ["ffmpeg", "-y", "-nostdin", "-headers", f"User-Agent: {_REQ_HEADERS['User-Agent']}\r\n",
                   "-i", video_s["url"], "-headers", f"User-Agent: {_REQ_HEADERS['User-Agent']}\r\n", "-i", audio_s["url"],
                   "-c:v", "copy", "-c:a", "aac", "-shortest", out]
            success, err = _run_ffmpeg(cmd, timeout=900)
            if success and os.path.exists(out) and os.path.getsize(out) > 0:
                return out, info, None
            return None, info, err
    except Exception as e:
        print(f"[download video Piped] {e}")
    return _yt_dlp_download_video(link, quality)


def _yt_dlp_download_video(link: str, quality=720):
    fmt = f"bestvideo[height<=?{quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<=?{quality}]/best"
    last = "فشل تحميل الفيديو"
    for s in _YTDLP_STRATEGIES:
        try:
            opts = {"format": fmt, "outtmpl": "/tmp/%(title).70s.%(ext)s", "merge_output_format": "mp4",
                    "quiet": True, "no_warnings": True, "nocheckcertificate": True, "cachedir": False,
                    "extractor_args": s["extractor_args"], "http_headers": s["http_headers"]}
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(link, download=True)
                file = ydl.prepare_filename(data)
                base = os.path.splitext(file)[0]
                if not os.path.exists(file) and os.path.exists(base + ".mp4"):
                    file = base + ".mp4"
                if os.path.exists(file):
                    return file, {"title": data.get("title"), "duration_seconds": int(data.get("duration") or 0)}, None
        except Exception as e:
            last = str(e)[:250]
    return None, None, last


def audio_opts(outtmpl: str = "/tmp/%(title).70s.%(ext)s") -> dict:
    return {"format": AUDIO_FORMAT, "outtmpl": outtmpl, "quiet": True, "no_warnings": True, "nocheckcertificate": True}
