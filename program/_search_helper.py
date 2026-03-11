import json
import asyncio
from driver.utils import bash

try:
    from youtubesearchpython import VideosSearch
    _USE_VSP = True
except ImportError:
    _USE_VSP = False

try:
    from youtube_search import YoutubeSearch
    _USE_YS = True
except ImportError:
    _USE_YS = False


async def ytsearch(query: str):
    loop = asyncio.get_event_loop()
    try:
        if _USE_VSP:
            def _s():
                r = VideosSearch(query, limit=1).result()
                if not r or not r.get("result"):
                    return None
                v = r["result"][0]
                th = v.get("thumbnails", [{}])
                return [v.get("title","Unknown"), v.get("link",""), v.get("duration","0:00") or "0:00", th[0].get("url","") if th else ""]
            res = await loop.run_in_executor(None, _s)
            return res if res else "no results"
        elif _USE_YS:
            def _s2():
                r = YoutubeSearch(query, max_results=1).to_dict()
                if not r: return None
                v = r[0]
                return [v.get("title","Unknown"), "https://www.youtube.com"+v.get("url_suffix",""), v.get("duration","0:00"), (v.get("thumbnails") or [""])[0]]
            res = await loop.run_in_executor(None, _s2)
            return res if res else "no results"
        else:
            out, err = await bash(f'yt-dlp "ytsearch1:{query}" --dump-json --no-playlist --no-download --no-warnings --ignore-errors')
            if not out.strip(): return err[:200] if err else "no output"
            d = json.loads(out.strip().split("\n")[0])
            m, s = divmod(int(d.get("duration",0)), 60)
            return [d.get("title","Unknown"), d.get("webpage_url",""), f"{m}:{s:02d}", d.get("thumbnail","")]
    except Exception as e:
        return str(e)


async def ytdl_audio(link: str):
    # نجرب فورمات مختلفة لو فيه مشكلة
    for fmt in ["bestaudio/best", "bestaudio", "best", "worstaudio"]:
        out, err = await bash(f'yt-dlp -g -f "{fmt}" --no-warnings "{link}"')
        out = out.strip().split("\n")[0].strip() if out else ""
        if out and out.startswith("http"):
            return 1, out
    return 0, err


async def ytdl_video(link: str):
    for fmt in ["best[height<=720]/best", "best[height<=480]/best", "best"]:
        out, err = await bash(f'yt-dlp -g -f "{fmt}" --no-warnings "{link}"')
        out = out.strip().split("\n")[0].strip() if out else ""
        if out and out.startswith("http"):
            return 1, out
    return 0, err
