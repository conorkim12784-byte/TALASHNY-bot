import json, subprocess
from pyrogram import Client, errors
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)


@Client.on_inline_query()
async def inline(client: Client, query: InlineQuery):
    answers = []
    search_query = query.query.lower().strip().rstrip()

    if search_query == "":
        await client.answer_inline_query(
            query.id,
            results=answers,
            switch_pm_text=" يمكنك البحث مباشرة من اليوتيوب",
            switch_pm_parameter="help",
            cache_time=0,
        )
    else:
        try:
            result = subprocess.run(
                ["yt-dlp", f"ytsearch10:{search_query}", "--dump-json", "--no-playlist", "--no-download"],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                data = json.loads(line)
                duration_secs = data.get("duration", 0)
                mins, secs = divmod(int(duration_secs), 60)
                duration = f"{mins}:{secs:02d}"
                views = data.get("view_count", 0)
                answers.append(
                    InlineQueryResultArticle(
                        title=data.get("title", "Unknown"),
                        description=f"{duration}, {views:,} views.",
                        input_message_content=InputTextMessageContent(
                            "🔗 https://www.youtube.com/watch?v={}".format(data.get("id", ""))
                        ),
                        thumb_url=data.get("thumbnail", ""),
                    )
                )
        except Exception as e:
            print(e)

        try:
            await query.answer(results=answers, cache_time=0)
        except errors.QueryIdInvalid:
            await query.answer(
                results=answers,
                cache_time=0,
                switch_pm_text="خطاء:انتهت مهلة البحث",
                switch_pm_parameter="",
            )
