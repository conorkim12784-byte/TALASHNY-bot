import os
import aiohttp
import aiofiles
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from collections import Counter

W, H = 1280, 720

FONT       = "driver/source/regular.ttf"
FONT_BOLD  = "driver/source/medium.ttf"

# ── ألوان التصميم الأزرق الداكن ──────────────────────────
BG_TOP      = (2,   8,  24)
BG_BOT      = (5,  13,  46)
BLUE_DARK   = (13,  36,  96)
BLUE_MID    = (29,  78, 216)
BLUE_LIGHT  = (59, 130, 246)
BLUE_PALE   = (147, 197, 253)
TEXT_WHITE  = (239, 246, 255)
TEXT_MUTED  = (96,  165, 250)
TEXT_DIM    = (29,  78, 216)


def _load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _gradient_bg(size):
    """خلفية gradient أزرق داكن"""
    img = Image.new("RGBA", size)
    draw = ImageDraw.Draw(img)
    w, h = size
    for y in range(h):
        t = y / h
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))
    return img


def _rounded_rect(draw, xy, radius, fill, outline=None, outline_width=1):
    """مستطيل بزوايا مدورة"""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius,
                            fill=fill, outline=outline, width=outline_width)


def _glow_ellipse(base, cx, cy, rx, ry, color, alpha=80):
    """glow بنقطة ضوء"""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(80))
    base.alpha_composite(layer)


def _cover_rounded(cover_img, size=390, radius=30):
    """غلاف الألبوم مربع بزوايا مدورة"""
    cover_img = cover_img.resize((size, size)).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=radius, fill=255
    )
    out = Image.new("RGBA", (size, size))
    out.paste(cover_img, (0, 0), mask)
    return out


def _equalizer_bars(draw, x_start, y_base, count, color):
    """إيكوالايزر"""
    bar_w = 13
    gap   = 8
    for i in range(count):
        h = random.randint(28, 90)
        x = x_start + i * (bar_w + gap)
        alpha = 200
        draw.rounded_rectangle(
            [x, y_base - h, x + bar_w, y_base],
            radius=4,
            fill=(*color, alpha)
        )


def _progress_bar(draw, x, y, total_w, progress_ratio, color):
    """شريط التقدم"""
    # track
    draw.rounded_rectangle([x, y, x + total_w, y + 8], radius=4,
                            fill=(*BLUE_DARK, 255))
    # fill
    filled = int(total_w * progress_ratio)
    if filled > 0:
        draw.rounded_rectangle([x, y, x + filled, y + 8], radius=4,
                                fill=(*color, 255))
    # نقطة
    dot_x = x + filled
    r = 12
    draw.ellipse([dot_x - r, y + 4 - r, dot_x + r, y + 4 + r],
                 fill=(*BLUE_LIGHT, 255))
    draw.ellipse([dot_x - 5, y + 4 - 5, dot_x + 5, y + 4 + 5],
                 fill=(2, 8, 24, 255))


def dominant_color(img):
    small = img.resize((80, 80)).convert("RGB")
    pixels = list(small.getdata())
    # نتجاهل الألوان القريبة من الأسود أو الأبيض
    filtered = [p for p in pixels if not (
        all(c < 30 for c in p) or all(c > 225 for c in p)
    )]
    if not filtered:
        return BLUE_MID
    r, g, b = Counter(filtered).most_common(1)[0][0]
    return (r, g, b)


async def thumb(thumbnail, title, userid, ctitle,
                requester="", duration=0):
    """
    thumbnail  : URL صورة الألبوم
    title      : اسم الأغنية
    userid     : id المستخدم (للتخزين المؤقت)
    ctitle     : اسم المجموعة
    requester  : اسم من طلب الأغنية
    duration   : مدة الأغنية بالثواني (لشريط التقدم)
    """

    os.makedirs("search", exist_ok=True)
    path = f"search/{userid}.png"
    cover = None

    # تحقق من صحة الـ URL
    is_valid_url = (
        thumbnail
        and isinstance(thumbnail, str)
        and thumbnail.startswith(("http://", "https://"))
    )

    try:
        if not is_valid_url:
            raise ValueError("Invalid URL")
        async with aiohttp.ClientSession() as s:
            async with s.get(thumbnail, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    async with aiofiles.open(path, "wb") as f:
                        await f.write(await r.read())
                    cover = Image.open(path).convert("RGBA")
    except Exception:
        pass

    # ── بناء الخلفية ─────────────────────────────────────
    bg = _gradient_bg((W, H))

    # glow
    _glow_ellipse(bg, 280, 330, 320, 300, BLUE_DARK, alpha=100)
    _glow_ellipse(bg, 950, 580, 250, 200, BLUE_DARK, alpha=60)

    draw = ImageDraw.Draw(bg)

    # ── شريط accent جانبي ────────────────────────────────
    for i, alpha in enumerate(range(255, 0, -8)):
        draw.rectangle([72, 110 + i * 2, 78, 114 + i * 2],
                        fill=(*BLUE_MID, max(0, alpha)))

    # ── غلاف الألبوم ─────────────────────────────────────
    COVER_X, COVER_Y, COVER_SIZE = 80, 110, 420

    if cover:
        accent_color = dominant_color(cover)
        # glow بلون الغلاف
        _glow_ellipse(bg, COVER_X + COVER_SIZE // 2,
                      COVER_Y + COVER_SIZE // 2,
                      260, 260, accent_color, alpha=70)
        cover_img = _cover_rounded(cover, COVER_SIZE, radius=32)
        bg.paste(cover_img, (COVER_X, COVER_Y), cover_img)
    else:
        accent_color = BLUE_MID
        # مربع placeholder
        _rounded_rect(draw,
                      [COVER_X, COVER_Y,
                       COVER_X + COVER_SIZE, COVER_Y + COVER_SIZE],
                      radius=32,
                      fill=(*BLUE_DARK, 255),
                      outline=(*BLUE_MID, 160), outline_width=2)
        # أيقونة موسيقى
        note_font = _load_font(FONT_BOLD, 140)
        draw.text((COVER_X + COVER_SIZE // 2, COVER_Y + COVER_SIZE // 2 - 20),
                  "♫", font=note_font,
                  fill=(*BLUE_MID, 80), anchor="mm")

    # إطار الغلاف
    _rounded_rect(draw,
                  [COVER_X, COVER_Y,
                   COVER_X + COVER_SIZE, COVER_Y + COVER_SIZE],
                  radius=32, fill=None,
                  outline=(*BLUE_LIGHT, 80), outline_width=2)

    # ── خط فاصل عمودي ────────────────────────────────────
    SEP_X = 545
    for i, alpha in enumerate(range(180, 0, -3)):
        y = 80 + i * 2
        draw.rectangle([SEP_X, y, SEP_X + 1, y + 2],
                        fill=(*BLUE_MID, max(0, alpha)))

    # ── الجانب الأيمن: المعلومات ──────────────────────────
    INFO_X = 575
    now_time = datetime.now().strftime("%I:%M %p")

    # وقت الآن - badge
    _rounded_rect(draw, [INFO_X, 80, INFO_X + 200, 110],
                  radius=15,
                  fill=(*BLUE_DARK, 200),
                  outline=(*BLUE_MID, 120), outline_width=1)
    time_font = _load_font(FONT, 24)
    draw.text((INFO_X + 100, 95), f"⏰  {now_time}",
              font=time_font, fill=TEXT_MUTED, anchor="mm")

    # NOW PLAYING badge
    _rounded_rect(draw, [INFO_X, 128, INFO_X + 195, 158],
                  radius=15,
                  fill=(*BLUE_MID, 200))
    np_font = _load_font(FONT_BOLD, 22)
    draw.text((INFO_X + 98, 143), "NOW PLAYING",
              font=np_font, fill=(*BLUE_PALE, 255), anchor="mm")

    # اسم الأغنية
    title_font  = _load_font(FONT_BOLD, 58)
    text_font   = _load_font(FONT, 30)
    small_font  = _load_font(FONT, 26)

    song_title = title[:28] + ("…" if len(title) > 28 else "")
    draw.text((INFO_X, 185), song_title,
              font=title_font, fill=TEXT_WHITE)

    # خط فاصل
    draw.rectangle([INFO_X, 255, INFO_X + 310, 257],
                   fill=(*BLUE_MID, 100))

    # اسم المجموعة
    draw.text((INFO_X, 272), "▶  playing on",
              font=small_font, fill=TEXT_DIM)
    draw.text((INFO_X, 305), ctitle[:30],
              font=text_font, fill=TEXT_MUTED)

    # خط فاصل
    draw.rectangle([INFO_X, 345, INFO_X + 310, 347],
                   fill=(*BLUE_MID, 60))

    # من طلب الأغنية
    if requester:
        draw.text((INFO_X, 360), "👤  طلب بواسطة",
                  font=small_font, fill=TEXT_DIM)
        req_name = requester[:25] + ("…" if len(requester) > 25 else "")
        draw.text((INFO_X, 395), req_name,
                  font=text_font, fill=BLUE_PALE)

    # ── شريط التقدم ──────────────────────────────────────
    BAR_X = INFO_X
    BAR_Y = 455
    BAR_W = 620

    # نسبة التقدم عشوائية للعرض (الواقع: حسب الوقت)
    ratio = 0.42

    _progress_bar(draw, BAR_X, BAR_Y, BAR_W, ratio, BLUE_LIGHT)

    # وقت
    elapsed_s = int(duration * ratio)
    elapsed   = f"{elapsed_s // 60}:{elapsed_s % 60:02d}" if duration else "0:00"
    total_str = f"{duration // 60}:{duration % 60:02d}" if duration else "—:——"

    draw.text((BAR_X, BAR_Y + 22), elapsed,
              font=small_font, fill=TEXT_DIM)
    draw.text((BAR_X + BAR_W, BAR_Y + 22), total_str,
              font=small_font, fill=TEXT_DIM, anchor="ra")

    # ── إيكوالايزر ───────────────────────────────────────
    _equalizer_bars(draw, INFO_X, 610, 25, BLUE_LIGHT)

    # ── watermark ────────────────────────────────────────
    wm_font = _load_font(FONT_BOLD, 28)
    draw.text((W - 30, H - 28), "TALASHNY",
              font=wm_font,
              fill=(*BLUE_MID, 140),
              anchor="ra")

    # ── حفظ ──────────────────────────────────────────────
    out = f"search/final{userid}.png"
    bg.convert("RGB").save(out, quality=95)
    return out
