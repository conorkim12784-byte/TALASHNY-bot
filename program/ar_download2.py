"""
ar_download2.py
نسخة عربية لتحميل الفيديو مع PO Token + fallback.
"""

import os
import yt_dlp
from ytdl_utils import apply_pot_to_opts, POT_BASE_URL

DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FALLBACK_CLIENTS = [
    ["web_safari"],
    ["web"],
    ["mweb"],
    ["tv"],
    ["android"],
]


def download_video(url: str, quality: str = "best") -> str:
    """تحميل فيديو بجودة محددة. quality: best | 720 | 480 | 360"""
    fmt_map = {
        "best": "best[ext=mp4]/best",
        "720":  "best[height<=720][ext=mp4]/best[height<=720]",
        "480":  "best[height<=480][ext=mp4]/best[height<=480]",
        "360":  "best[height<=360][ext=mp4]/best[height<=360]",
    }
    fmt = fmt_map.get(str(quality), fmt_map["best"])
    output_template = os.path.join(DOWNLOAD_DIR, "%(id)s_%(height)sp.%(ext)s")

    last_error = None
    for clients in FALLBACK_CLIENTS:
        opts = {
            "format": fmt,
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }
        opts = apply_pot_to_opts(opts)
        opts["extractor_args"]["youtube"]["player_client"] = clients
        opts["extractor_args"]["youtube"]["getpot_bgutil_baseurl"] = [POT_BASE_URL]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            last_error = e
            print(f"[ar_download2] فشلت محاولة {clients}: {e}")
            continue

    raise RuntimeError(f"تعذّر تحميل الفيديو. آخر خطأ: {last_error}")
