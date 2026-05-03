"""
Helper مركزي لإنشاء أزرار Inline ملوّنة.

تيليجرام أضاف فيتشر تلوين الأزرار في Bot API (Layer 224+):
  - PRIMARY  → أزرق
  - SUCCESS  → أخضر
  - DANGER   → أحمر
  - DEFAULT  → الافتراضي (رمادي/شفاف)

المكتبة المستخدمة هنا هي `pyrotgfork` (نفس API بتاع pyrofork، بس Layer 225).

استخدام:
    from program.utils.colored_buttons import btn, BTN
    BTN("موافق", "yes", "success")
    BTN("رفض", "no", "danger")
    BTN("معلومات", "info", "primary")
    BTN("رجوع", "back")  # default

الـ helper كمان آمن: لو المكتبة المركّبة ما تدعمش `style`، بيرجع زر عادي.
"""

from typing import Optional
from pyrogram.types import InlineKeyboardButton

try:
    from pyrogram.enums import ButtonStyle  # type: ignore
    _HAS_STYLE = True
except Exception:
    ButtonStyle = None  # type: ignore
    _HAS_STYLE = False


def _resolve(style: Optional[str]):
    if not _HAS_STYLE or not style:
        return None
    s = style.strip().lower()
    mapping = {
        "primary": ButtonStyle.PRIMARY,
        "blue": ButtonStyle.PRIMARY,
        "info": ButtonStyle.PRIMARY,
        "success": ButtonStyle.SUCCESS,
        "green": ButtonStyle.SUCCESS,
        "ok": ButtonStyle.SUCCESS,
        "danger": ButtonStyle.DANGER,
        "red": ButtonStyle.DANGER,
        "warn": ButtonStyle.DANGER,
        "default": ButtonStyle.DEFAULT,
        "gray": ButtonStyle.DEFAULT,
    }
    return mapping.get(s, ButtonStyle.DEFAULT)


def BTN(
    text: str,
    callback_data: Optional[str] = None,
    style: Optional[str] = None,
    *,
    url: Optional[str] = None,
):
    """ينشئ InlineKeyboardButton ملوّن (لو المكتبة بتدعم).

    text: نص الزر
    callback_data: للـ callback queries
    style: 'primary' | 'success' | 'danger' | 'default'
    url: لو الزر URL بدل callback
    """
    # افتراضي: أي زر مش محدد لون يبقى أزرق (primary)
    if not style:
        style = "primary"
    s = _resolve(style)
    kwargs = {"text": text}
    if url:
        kwargs["url"] = url
    elif callback_data is not None:
        kwargs["callback_data"] = callback_data
    if s is not None:
        kwargs["style"] = s
    try:
        return InlineKeyboardButton(**kwargs)
    except TypeError:
        # fallback: المكتبة لا تدعم style — ارجع بدون اللون
        kwargs.pop("style", None)
        return InlineKeyboardButton(**kwargs)


# alias قصير
btn = BTN
