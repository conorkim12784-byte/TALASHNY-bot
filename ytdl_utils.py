# yt-dlp config بدون بروكسي (يمشي حاله)

COMMON = {
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "geo_bypass": True,
    "geo_bypass_country": "US",

    "http_headers": {
        "User-Agent": "com.google.android.youtube/17.31.35 (Linux; U; Android 11)",
        "Accept-Language": "en-US,en;q=0.9"
    },

    "sleep_interval": 5,
    "max_sleep_interval": 10,
    "retries": 10,

    "extractor_args": {
        "youtube": {
            "player_client": ["android"]
        }
    }
}

def audio_opts(out_tpl="/tmp/%(title)s.%(ext)s"):
    return {**COMMON, "format": "bestaudio/best", "outtmpl": out_tpl}

def video_opts(out_tpl="/tmp/%(title)s.%(ext)s"):
    return {**COMMON, "format": "best[ext=mp4]/best", "outtmpl": out_tpl}
