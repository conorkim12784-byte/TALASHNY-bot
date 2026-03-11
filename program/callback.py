# Copyright (C) 2022 By Shadow

from driver.queues import QUEUE
from pyrogram import Client, filters
from program.utils.inline import menu_markup
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    BOT_PHOTO,
    ASSISTANT_NAME,
    BOT_NAME,
    BOT_USERNAME,
    GROUP_SUPPORT,
    OWNER_NAME,
    UPDATES_CHANNEL,
)


@Client.on_callback_query(filters.regex("cbstart"))
async def cbstart(_, query: CallbackQuery):
    await query.answer("الصفحه الرئيسيه")
    await query.edit_message_caption(
        caption=f"""━━━━━━━━━━━━━━━━━━━━
T·A·L·A·S·H·N·Y  —  بـوت الـمـوسـيـقـى
━━━━━━━━━━━━━━━━━━━━

اهـلا  {query.from_user.mention()} !

انـا بـوت تـلاشـنـي للـمـوسـيـقـى
اشـغّـل الاغـانـي فـي الـمـكـالـمـات الـصـوتـيـة
بـجـودة عـالـيـة وبـدون انـقـطـاع

يـدعـم الاوامـر بـالـعـربـي والانـجـلـيـزي
اضـفـنـي للـمـجـمـوعـة وارفـعـنـي ادمـن
اكـتـب /انـضـم لـدعـوة الـحـسـاب الـمـسـاعـد

━━━━━━━━━━━━━━━━━━━━""",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "اضـف الـبـوت لـمـجـمـوعـتـك",
                    url=f"https://t.me/G_FireBot?startgroup=true")],
                [
                    InlineKeyboardButton("الاوامر", url="https://telegra.ph/%F0%9D%99%B2%E1%B4%8F%E1%B4%8D%E1%B4%8D%E1%B4%80%C9%B4%E1%B4%85s-04-06"),
                    InlineKeyboardButton("المطور", url=f"https://t.me/{OWNER_NAME}"),
                ],
                [
                    InlineKeyboardButton("جروب الدعم", url=f"https://t.me/{GROUP_SUPPORT}"),
                    InlineKeyboardButton("قناة البوت", url=f"https://t.me/{UPDATES_CHANNEL}"),
                ],
                [InlineKeyboardButton("كيفية الاستخدام", callback_data="cbhowtouse")],
            ]
        ),
    )


@Client.on_callback_query(filters.regex("cbhowtouse"))
async def cbguides(_, query: CallbackQuery):
    await query.answer("طريقة الاستخدام")
    await query.edit_message_caption(
        caption=f"""━━━━━━━━━━━━━━━━━━━━
كـيـفـيـة  الاسـتـخـدام
━━━━━━━━━━━━━━━━━━━━

١  —  اضـفـنـي الـى مـجـمـوعـتـك
٢  —  ارفـعـنـي ادمـن مـع كـامـل الـصـلاحـيـات
٣  —  اكـتـب /reload لـتـحـديـث بـيـانـات الـمـشـرفـيـن
٤  —  اكـتـب /انـضـم لـدعـوة الـحـسـاب الـمـسـاعـد
٥  —  شـغّـل الـمـكـالـمـة اولا ثـم ابـدا الـتـشـغـيـل
٦  —  اسـتـخـدم /reload اذا واجـهـت اي مـشـكـلـة

اذا لـم يـنـضـم الـبـوت الـى الـمـكـالـمـة
اكـتـب /userbotleave ثـم /userbotjoin

لـلـدعـم والاسـتـفـسـار  —  @{GROUP_SUPPORT}
قـنـاة الـبـوت  —  @{UPDATES_CHANNEL}

━━━━━━━━━━━━━━━━━━━━""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("رجوع", callback_data="cbstart")]]
        ),
    )


@Client.on_callback_query(filters.regex("cbcmds"))
async def cbcmds(_, query: CallbackQuery):
    await query.answer("قائمة الاوامر")
    await query.edit_message_text(
        f"""» **قم بالضغط علي الزر الذي تريده لمعرفه الاوامر لكل فئه منهم !**

⚡ قناة البوت @{UPDATES_CHANNEL}""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👷🏻 اوامر الادمنيه", callback_data="cbadmin"),
                    InlineKeyboardButton("🧙🏻 اوامر المطور", callback_data="cbsudo"),
                ],[
                    InlineKeyboardButton("📚 اوامر اساسيه", callback_data="cbbasic")
                ],[
                    InlineKeyboardButton("🔙 رجوع", callback_data="cbstart")
                ],
            ]
        ),
    )


@Client.on_callback_query(filters.regex("cbbasic"))
async def cbbasic(_, query: CallbackQuery):
    await query.answer("الاوامر الاساسيه")
    await query.edit_message_text(
        f"""🏮 الاوامر الاساسيه:

» /play +「اسم الأغنية / رابط」لتشغيل اغنيه في المحادثه الصوتيه
» /vplay +「اسم الفيديو / رابط 」 لتشغيل الفيديو داخل المكالمة
» /vstream 「رابط」 تشغيل فيديو مباشر من اليوتيوب
» /playlist 「تظهر لك قائمة التشغيل」
» /end「لإنهاء الموسيقى / الفيديو في الكول」
» /song + 「الاسم تنزيل صوت من youtube」
»/vsong + 「الاسم  تنزيل فيديو من youtube」
» /skip「للتخطي إلى التالي」
» /ping 「إظهار حالة البوت بينغ」
» /uptime 「لعرض مده التشغيل للبوت」
» /alive「اظهار معلومات البوت(في المجموعه)」
⚡ قناة البوت @{UPDATES_CHANNEL}""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 رجوع", callback_data="cbcmds")]]
        ),
    )



@Client.on_callback_query(filters.regex("cbadmin"))
async def cbadmin(_, query: CallbackQuery):
    await query.answer("اوامر الادمنيه")
    await query.edit_message_text(
        f"""🏮 هنا أوامر الادمنيه:

» /pause 「ايقاف التشغيل موقتآ」
» /resume 「استئناف التشغيل」
» /stop「لإيقاف التشغيل」
» /vmute 「لكتم البوت」
» /vunmute 「لرفع الكتم عن البوت」
» /volume 「ضبط مستوئ الصوت」
» /reload「لتحديث البوت و قائمة المشرفين」
» /userbotjoin「لاستدعاء الحساب المساعد」
» /userbotleave「لطرد الحساب المساعد」
⚡ قناة البوت @{UPDATES_CHANNEL}""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 رجوع", callback_data="cbcmds")]]
        ),
    )

@Client.on_callback_query(filters.regex("cbsudo"))
async def cbsudo(_, query: CallbackQuery):
    await query.answer("اوامر المطور")
    await query.edit_message_text(
        f"""🏮 هنا اوامر المطور:

» /rmw「لحذف جميع الملفات 」
» /rmd「حذف جميع الملفات المحمله」
» /sysinfo「لمعرفه معلومات السيرفر」
» /update「لتحديث بوتك لاخر نسخه」
» /restart「اعاده تشغيل البوت」
» /leaveall「خروج الحساب المساعد من جميع المجموعات」

⚡ قناة البوت @{UPDATES_CHANNEL}""",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 رجوع", callback_data="cbcmds")]]
        ),
    )


@Client.on_callback_query(filters.regex("cbmenu"))
async def cbmenu(_, query: CallbackQuery):
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not getattr(a, "can_manage_video_chats", getattr(a, "can_manage_voice_chats", True)):
        return await query.answer("💡 المسؤول الوحيد الذي لديه إذن إدارة الدردشات الصوتية يمكنه النقر على هذا الزر !", show_alert=True)
    chat_id = query.message.chat.id
    user_id = query.message.from_user.id
    buttons = menu_markup(user_id)
    chat = query.message.chat.title
    if chat_id in QUEUE:
          await query.edit_message_text(
              f"⚙️ **الإعدادات** {query.message.chat.title}\n\n⏸ : ايقاف التشغيل موقتآ\n▶️ : استئناف التشغيل\n🔇 : كتم الصوت\n🔊 : الغاء كتم الصوت\n⏹ : ايقاف التشغيل",
              reply_markup=InlineKeyboardMarkup(buttons),
          )
    else:
        await query.answer("❌ قائمة التشغيل فارغه", show_alert=True)


@Client.on_callback_query(filters.regex("cls"))
async def close(_, query: CallbackQuery):
    a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
    if not getattr(a, "can_manage_video_chats", getattr(a, "can_manage_voice_chats", True)):
        return await query.answer("💡 المسؤول الوحيد الذي لديه إذن إدارة الدردشات الصوتية يمكنه النقر على هذا الزر !", show_alert=True)
    await query.message.delete()
