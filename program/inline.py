# inline.py — بحث inline بدون API أو proxy

import asyncio
from pyrogram import Client, errors
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)


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
        from youtubesearchpython import VideosSearch
        results = await asyncio.to_thread(lambda: VideosSearch(search_query, limit=10).result())
        items = results.get("result", [])

        for item in items:
            vid_id = item.get("id") or item.get("link", "").split("v=")[-1].split("&")[0]
            title = item.get("title", "")
            thumbs = item.get("thumbnails") or []
            thumbnail = thumbs[-1].get("url") if thumbs else ""
            duration = item.get("duration") or "0:00"
            views_raw = (item.get("viewCount") or {}).get("text") or "0"
            answers.append(
                InlineQueryResultArticle(
                    title=title,
                    description=f"{duration}, {views_raw} views.",
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
