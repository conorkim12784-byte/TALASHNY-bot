import asyncio
from pyrogram import Client, errors
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from program.ytsearch_core import search_youtube_async


@Client.on_inline_query()
async def inline(client: Client, query: InlineQuery):
    answers = []
    search_query = query.query.lower().strip()
    if not search_query:
        await client.answer_inline_query(query.id, results=answers,
            switch_pm_text="يمكنك البحث مباشرة من اليوتيوب", switch_pm_parameter="help", cache_time=0)
        return
    try:
        items = await search_youtube_async(search_query, limit=10)
        for item in items:
            answers.append(InlineQueryResultArticle(
                title=item["title"],
                description=f"{item['duration']}, {item['views']}",
                input_message_content=InputTextMessageContent(f"🔗 {item['url']}"),
                thumb_url=item["thumbnail"],
            ))
    except Exception as e:
        print(f"[inline search error] {e}")
    try:
        await query.answer(results=answers, cache_time=0)
    except errors.QueryIdInvalid:
        await query.answer(results=answers, cache_time=0,
            switch_pm_text="خطأ: انتهت مهلة البحث", switch_pm_parameter="")
