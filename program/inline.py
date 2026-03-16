# inline.py - بحث inline عبر YouTube Data API v3
import asyncio
import re as _re
import requests as _req
from pyrogram import Client, errors
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

TOR_PROXY = "socks5://127.0.0.1:9050"


@Client.on_inline_query()
async def inline(client: Client, query: InlineQuery):
    answers = []
    search_query = query.query.lower().strip()

    if not search_query:
        await client.answer_inline_query(
            query.id,
            results=answers,
            switch_pm_text="يمكنك البحث مباشرة من اليوتيوب",
            switch_pm_parameter="help",
            cache_time=0,
        )
        return

    try:
        from config import YOUTUBE_API_KEY
        r = await asyncio.to_thread(
            lambda: _req.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "snippet", "q": search_query, "type": "video",
                        "maxResults": 10, "key": YOUTUBE_API_KEY},
                timeout=10,
                proxies={"http": TOR_PROXY, "https": TOR_PROXY},
            )
        )
        r.raise_for_status()
        items = r.json().get("items", [])

        if items:
            ids = ",".join(i["id"]["videoId"] for i in items)
            r2 = await asyncio.to_thread(
                lambda: _req.get(
                    "https://www.googleapis.com/youtube/v3/videos",
                    params={"part": "contentDetails,statistics", "id": ids, "key": YOUTUBE_API_KEY},
                    timeout=10,
                    proxies={"http": TOR_PROXY, "https": TOR_PROXY},
                )
            )
            r2.raise_for_status()
            details = {d["id"]: d for d in r2.json().get("items", [])}

            for item in items:
                vid_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                thumbnail = item["snippet"]["thumbnails"].get("high", {}).get("url", "")
                detail = details.get(vid_id, {})
                iso = detail.get("contentDetails", {}).get("duration", "PT0S")
                mt = _re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
                h, mn, s = (int(mt.group(i) or 0) for i in (1, 2, 3)) if mt else (0, 0, 0)
                total = h * 3600 + mn * 60 + s
                mins, secs = divmod(total, 60)
                duration = f"{mins}:{secs:02d}"
                views = int(detail.get("statistics", {}).get("viewCount", 0))
                answers.append(
                    InlineQueryResultArticle(
                        title=title,
                        description=f"{duration}, {views:,} views.",
                        input_message_content=InputTextMessageContent(
                            f"🔗 https://www.youtube.com/watch?v={vid_id}"
                        ),
                        thumb_url=thumbnail,
                    )
                )
    except Exception as e:
        print(f"[inline search error] {e}")

    try:
        await query.answer(results=answers, cache_time=0)
    except errors.QueryIdInvalid:
        await query.answer(
            results=answers,
            cache_time=0,
            switch_pm_text="خطأ: انتهت مهلة البحث",
            switch_pm_parameter="",
        )
