"""
ytdl_utils.py
Helpers لإعداد yt-dlp مع PO Token (bgutil provider) لتجاوز
رسالة: "Sign in to confirm you're not a bot".

نستخدم سيرفر POT المحلي (bgutil-ytdlp-pot-provider) المُشغّل داخل الكونتينر
على المنفذ 4416. الإعدادات هنا تُمرَّر داخل أي yt-dlp options قبل التشغيل.
"""

import os

# عنوان سيرفر POT المحلي (يتم تشغيله من Dockerfile)
POT_BASE_URL = os.environ.get("POT_BASE_URL", "http://127.0.0.1:4416")


def get_pot_extractor_args() -> dict:
    """
    يُرجع extractor_args الخاصة بـ yt-dlp لتفعيل PO Token عبر bgutil.
    استراتيجيات player_client مرتبة من الأنجح للأقل نجاحاً حالياً.
    """
    return {
        "youtube": {
            # استراتيجيات تشغيل متعددة - yt-dlp سيجرّبها بالترتيب
            "player_client": ["web_safari", "web", "mweb", "tv"],
            # تمرير عنوان سيرفر POT لمزود bgutil
            "getpot_bgutil_baseurl": [POT_BASE_URL],
        },
        "youtubepot-bgutilhttp": {
            "base_url": [POT_BASE_URL],
        },
    }


def apply_pot_to_opts(ydl_opts: dict) -> dict:
    """
    يدمج إعدادات PO Token داخل ydl_opts الموجودة (دون مسح أي قيم سابقة).
    استدعِ هذه الدالة قبل تمرير الـ opts إلى YoutubeDL.
    """
    if ydl_opts is None:
        ydl_opts = {}

    existing = ydl_opts.get("extractor_args") or {}
    pot_args = get_pot_extractor_args()

    # دمج عميق بسيط (المفاتيح الجديدة تُستبدل، والباقي يبقى)
    merged = {**existing}
    for key, value in pot_args.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value

    ydl_opts["extractor_args"] = merged

    # إعدادات إضافية تساعد على الثبات
    ydl_opts.setdefault("retries", 3)
    ydl_opts.setdefault("fragment_retries", 3)
    ydl_opts.setdefault("nocheckcertificate", True)
    ydl_opts.setdefault("geo_bypass", True)

    return ydl_opts
