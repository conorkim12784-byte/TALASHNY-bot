from driver.queues import QUEUE
from pyrogram import Client, filters
from program.utils.inline import menu_markup
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    BOT_PHOTO, ASSISTANT_NAME, BOT_NAME, BOT_USERNAME,
    GROUP_SUPPORT, OWNER_NAME, UPDATES_CHANNEL,
)


@Client.on_callback_query(filters.regex("cbstart"))
async def cbstart(_, query: CallbackQuery):
    await query.answer("الصفحه الرئيسيه")
    await query.edit_message_text(
        f"**━━━━━━━━━━━━\n"
        f"اهـلا يـبـنـي {query.from_user.mention()} !\n"
        "مـرحبآ بـك انا بـوت اقـوم بـتـشـغـيـل الاغـانـي فـي الـمـكـالـمـه الـصـوتـيـه\n"
        "يـمـكـنـنـي الـتـشـغـيـل بـصـوت رائـع وبـدون اي مـشـاكـل\n"
        "+ اضـفـنـي الـى مـجـمـوعـتـك وارفـعـنـي ادمـن مـع كـامـل الـصـلاحـيـات\n"
        "البـوت يـشـتـغـل بـالاوامـر عـربـي وانـجـلـيـزي\n"
        "لانـضـمـام الـحـسـاب الـمـسـاعـد اكـتـب انـضـم\n\n"
        "[ძᥲᖇᥱძᥱ᥎Ꭵᥣ](https://t.me/FY_TF)\n"
        "━━━━━━━━━━━━━━━━━━**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ضيـف البـوت لمجمـوعتـك ✔",
                url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [
                InlineKeyboardButton("الاوامر",
                    url="https://telegra.ph/%F0%9D%99%B2%E1%B4%8F%E1%B4%8D%E1%B4%8D%E1%B4%80%C9%B4%E1%B4%85s-04-06"),
                InlineKeyboardButton(" المطور", url=f"https://t.me/{OWNER_NAME}"),
            ],
            [
                InlineKeyboardButton(" جروب الدعم", url=f"https://t.me/{GROUP_SUPPORT}"),
                InlineKeyboardButton(" قناة البوت", url=f"https://t.me/{UPDATES_CHANNEL}"),
            ],
        ]),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(filters.regex("cbhowtouse"))
async def cbguides(_, query: CallbackQuery):
    await query.answer("طريقة الاستخدام")
    await query.edit_message_text(
        f" الدليل الأساسي لاستخدام هذا البوت:\n\n"
        " 1 ↤ أضفني إلى مجموعتك\n"
        " 2 ↤ ارفعني مشرفاً مع كامل الصلاحيات\n"
        " 3 ↤ اكتب /reload لتحديث بيانات المشرفين\n"
        f" 4 ↤ أضف @{ASSISTANT_NAME} أو اكتب /userbotjoin\n"
        " 5 ↤ شغّل المكالمة الصوتية أولاً\n"
        " 6 ↤ في حالة مشاكل استخدم /userbotleave ثم /userbotjoin\n\n"
        f" 💡 لأي أسئلة ↤ @{GROUP_SUPPORT}\n\n"
        f"⚡ قناة البوت @{UPDATES_CHANNEL}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 رجوع", callback_data="cbstart")]]
        ),
    )


@Client.on_callback_query(filters.regex("cbcmds"))
async def cbcmds(_, query: CallbackQuery):
    await query.answer("قائمة الاوامر")
    await query.edit_message_text(
        f"» **قم بالضغط علي الزر الذي تريده لمعرفه الاوامر لكل فئه !**\n\n"
        f"⚡ قناة البوت @{UPDATES_CHANNEL}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(" اوامر الادمنيه", callback_data="cbadmin"),
                InlineKeyboardButton(" اوامر المطور", callback_data="cbsudo"),
            ],
            [InlineKeyboardButton(" اوامر اساسيه", callback_data="cbbasic")],
            [InlineKeyboardButton(" رجوع", callback_data="cbstart")],
        ]),
    )


@Client.on_callback_query(filters.regex("cbbasic"))
async def cbbasic(_, query: CallbackQuery):
    await query.answer("الاوامر الاساسيه")
    await query.edit_message_text(
        f"🏮 الاوامر الاساسيه:\n\n"
        "» /play +「اسم الأغنية / رابط」لتشغيل اغنيه\n"
        "» /vplay +「اسم الفيديو / رابط」لتشغيل فيديو\n"
        "» /vstream 「رابط」تشغيل فيديو مباشر\n"
        "» /playlist 「قائمة التشغيل」\n"
        "» /end「لإنهاء التشغيل」\n"
        "» /song + 「الاسم」تنزيل صوت من youtube\n"
        "» /vsong + 「الاسم」تنزيل فيديو من youtube\n"
        "» /skip「للتخطي إلى التالي」\n"
        "» /ping 「حالة البوت」\n"
        "» /uptime 「مده تشغيل البوت」\n"
        f"⚡ قناة البوت @{UPDATES_CHANNEL}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 رجوع", callback_data="cbcmds")]]
        ),
    )


@Client.on_callback_query(filters.regex("cbadmin"))
async def cbadmin(_, query: CallbackQuery):
    await query.answer("اوامر الادمنيه")
    await query.edit_message_text(
        f"🏮 هنا أوامر الادمنيه:\n\n"
        "» /pause 「ايقاف التشغيل موقتآ」\n"
        "» /resume 「استئناف التشغيل」\n"
        "» /stop「لإيقاف التشغيل」\n"
        "» /mute 「لكتم البوت」\n"
        "» /unmute 「لرفع الكتم」\n"
        "» /volume 「ضبط مستوى الصوت」\n"
        "» /reload「تحديث قائمة المشرفين」\n"
        "» /userbotjoin「استدعاء الحساب المساعد」\n"
        "» /userbotleave「طرد الحساب المساعد」\n"
        f"⚡ قناة البوت @{UPDATES_CHANNEL}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 رجوع", callback_data="cbcmds")]]
        ),
    )


@Client.on_callback_query(filters.regex("cbsudo"))
async def cbsudo(_, query: CallbackQuery):
    await query.answer("اوامر المطور")
    await query.edit_message_text(
        f"🏮 هنا اوامر المطور:\n\n"
        "» /rmw「لحذف الملفات المؤقتة」\n"
        "» /rmd「حذف الملفات المحمله」\n"
        "» /sysinfo「معلومات السيرفر」\n"
        "» /update「تحديث البوت」\n"
        "» /restart「اعاده تشغيل البوت」\n"
        "» /leaveall「خروج المساعد من جميع المجموعات」\n"
        "» /eval「تشغيل كود」\n"
        "» /sh「تشغيل امر في السيرفر」\n\n"
        f"⚡ قناة البوت @{UPDATES_CHANNEL}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(" رجوع", callback_data="cbcmds")]]
        ),
    )


@Client.on_callback_query(filters.regex("cbmenu"))
async def cbmenu(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    try:
        a = await _.get_chat_member(chat_id, query.from_user.id)
        if not (a.privileges and a.privileges.can_manage_video_chats):
            return await query.answer(
                "💡 يجب أن تكون مشرفاً لاستخدام هذا الزر!", show_alert=True
            )
    except Exception:
        return await query.answer("✘ تعذر التحقق من صلاحياتك", show_alert=True)

    user_id = query.from_user.id
    buttons = menu_markup(user_id)

    if chat_id in QUEUE:

        text = (
            f"╭────⌁ 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦 \n"
            f"│╭────────────⟢\n"
            f"╞╡A-⏸ ايقاف التشغيل مؤقتاً\n"
            f"╞╡B-▶️ استئناف التشغيل\n"
            f"╞╡C-⏹ ايقاف التشغيل\n"
            f"╞╡D-🔊 الغاء كتم الصوت\n"
            f"╞╡E-🔇 كتم الصوت\n"
            f"│╰────────────⟢\n"
            f"╰────⌁ 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦 "
        )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    else:
        await query.answer("✘ قائمة التشغيل فارغه", show_alert=True)

@Client.on_callback_query(filters.regex("cls"))
async def close(_, query: CallbackQuery):
    try:
        a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
        if not (a.privileges and a.privileges.can_manage_video_chats):
            return await query.answer(
                "💡 يجب أن تكون مشرفاً لاستخدام هذا الزر!", show_alert=True
            )
    except Exception:
        pass
    await query.message.delete()
