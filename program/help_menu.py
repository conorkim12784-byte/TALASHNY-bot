
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

START_TEXT = "اهلا بك في بوت الموسيقى\nاختر القسم"

buttons = InlineKeyboardMarkup(
[
[InlineKeyboardButton("اوامر التشغيل",callback_data="help_play")],
[InlineKeyboardButton("اوامر الادمن",callback_data="help_admin")],
[InlineKeyboardButton("اوامر المطور",callback_data="help_dev")]
]
)

@Client.on_message(filters.command("help"))
async def help_menu(client, message):
    await message.reply_text(START_TEXT, reply_markup=buttons)


@Client.on_callback_query(filters.regex("help_play"))
async def play_help(client,query):
    txt = '''
اوامر الاعضاء:

/play - تشغيل اغنية
/vplay - تشغيل فيديو
/song - تحميل اغنية
/search - بحث
/queue - قائمة التشغيل
/incall - من في الكول
'''
    await query.message.edit_text(txt)


@Client.on_callback_query(filters.regex("help_admin"))
async def admin_help(client,query):
    txt = '''
اوامر المشرفين:

/pause
/resume
/skip
/stop
'''
    await query.message.edit_text(txt)


@Client.on_callback_query(filters.regex("help_dev"))
async def dev_help(client,query):
    txt = '''
اوامر المطور:

/broadcast
/leaveall
/botadmin
/rmbotadmin
'''
    await query.message.edit_text(txt)
