"""
downloader.py
تحميل صوت/فيديو من يوتيوب مع PO Token.
يحاول عدة استراتيجيات (player clients) قبل الفشل.
"""

import os
import yt_dlp
from ytdl_utils import apply_pot_to_opts, POT_BASE_URL

DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# استراتيجيات بالترتيب: الأنجح أولاً
FALLBACK_CLIENTS = [
    ["web_safari"],
    ["web"],
    ["mweb"],
    ["tv"],
    ["android"],
]


def _base_opts(is_audio: bool, output_template: str) -> dict:
    if is_audio:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:
        opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }
    return apply_pot_to_opts(opts)


def download(url: str, is_audio: bool = True) -> str:
    """يُحمّل الفيديو/الصوت ويُرجع مسار الملف الناتج."""
    output_template = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    last_error = None

    for clients in FALLBACK_CLIENTS:
        opts = _base_opts(is_audio, output_template)
        # نُعدّل player_client لكل محاولة
        opts["extractor_args"]["youtube"]["player_client"] = clients
        opts["extractor_args"]["youtube"]["getpot_bgutil_baseurl"] = [POT_BASE_URL]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if is_audio:
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp3"
                return filename
        except Exception as e:
            last_error = e
            print(f"[downloader] فشلت محاولة {clients}: {e}")
            continue

    raise RuntimeError(f"كل محاولات التحميل فشلت. آخر خطأ: {last_error}")
