"""
_search_helper.py
دالة بحث مساعدة على يوتيوب مع تفعيل PO Token تلقائياً.
"""

import yt_dlp
from ytdl_utils import apply_pot_to_opts


def search_youtube(query: str, max_results: int = 5):
    """يبحث على يوتيوب ويُرجع قائمة نتائج (id, title, url, duration)."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "default_search": f"ytsearch{max_results}",
    }
    ydl_opts = apply_pot_to_opts(ydl_opts)

    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        entries = info.get("entries", []) if info else []
        for entry in entries:
            if not entry:
                continue
            results.append({
                "id": entry.get("id"),
                "title": entry.get("title"),
                "url": entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}",
                "duration": entry.get("duration"),
            })
    return results
