import os
import aiohttp
import aiofiles
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from collections import Counter

try:
    import pytz
    CAIRO_TZ = pytz.timezone("Africa/Cairo")
except ImportError:
    CAIRO_TZ = None

W, H = 1280, 720

FONT        = "driver/source/regular.ttf"
FONT_BOLD   = "driver/source/medium.ttf"


def get_cairo_time() -> str:
    if CAIRO_TZ:
        now = datetime.now(CAIRO_TZ)
    else:
        # UTC+2 يدوي لو pytz مش موجود
        from datetime import timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=2)))
    return now.strftime("%I:%M %p")


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + radius*2, y1 + radius*2], fill=fill)
    draw.ellipse([x2 - radius*2, y1, x2, y1 + radius*2], fill=fill)
    draw.ellipse([x1, y2 - radius*2, x1 + radius*2, y2], fill=fill)
    draw.ellipse([x2 - radius*2, y2 - radius*2, x2, y2], fill=fill)


def rounded_image(img, size, radius=24):
    img = img.resize((size, size)).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0), mask)
    return out


def dominant_color(img):
    img = img.resize((80, 80)).convert("RGB")
    pixels = list(img.getdata())
    # نتجاهل الألوان الداكنة جداً
    pixels = [p for p in pixels if sum(p) > 60]
    if not pixels:
        return (80, 120, 255)
    r, g, b = Counter(pixels).most_common(1)[0][0]
    # نجعل اللون أكثر إشباعاً
    mx = max(r, g, b) or 1
    factor = 200 / mx
    return (min(int(r * factor), 255), min(int(g * factor), 255), min(int(b * factor), 255))


def draw_glow(base, color, x, y, size):
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse([x - size, y - size, x + size, y + size], fill=(*color, 80))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    base.alpha_composite(glow)


def draw_equalizer(draw, color, x_start, y_base, count=28, bar_w=8, gap=5):
    heights = [random.randint(15, 70) for _ in range(count)]
    for i, h in enumerate(heights):
        x = x_start + i * (bar_w + gap)
        alpha = random.randint(160, 230)
        draw.rectangle(
            [x, y_base - h, x + bar_w, y_base],
            fill=(*color, alpha)
        )


def draw_progress(draw, color, x, y, width, percent=0.45):
    # شريط خلفي
    draw.rounded_rectangle([x, y, x + width, y + 5], radius=3, fill=(255, 255, 255, 40))
    # شريط التقدم
    filled = int(width * percent)
    draw.rounded_rectangle([x, y, x + filled, y + 5], radius=3, fill=(*color, 220))
    # نقطة
    dot_x = x + filled
    draw.ellipse([dot_x - 7, y - 5, dot_x + 7, y + 10], fill=color)


async def thumb(thumbnail, title, userid, ctitle, requester=None, duration=0, **kwargs):

    os.makedirs("search", exist_ok=True)
    path = f"search/{userid}.png"
    cover = None

    # تحميل صورة الغلاف
    is_valid_url = (
        thumbnail
        and isinstance(thumbnail, str)
        and thumbnail.startswith(("http://", "https://"))
    )

    if is_valid_url:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(thumbnail, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        async with aiofiles.open(path, "wb") as f:
                            await f.write(await r.read())
                        cover = Image.open(path).convert("RGBA")
        except:
            cover = None

    # ===== الخلفية =====
    if cover:
        bg = cover.resize((W, H)).filter(ImageFilter.GaussianBlur(45))
        color = dominant_color(cover)
    else:
        bg = Image.new("RGBA", (W, H), (8, 10, 28))
        color = (80, 120, 255)

    # overlay داكن
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 160))
    bg.alpha_composite(overlay)

    # glow
    draw_glow(bg, color, 280, 340, 260)

    draw = ImageDraw.Draw(bg)

    # ===== صورة الغلاف — مربع بزوايا مدورة =====
    cover_size = 280
    cover_x, cover_y = 70, 180
    if cover:
        cover_sq = rounded_image(cover, cover_size, radius=22)
        bg.paste(cover_sq, (cover_x, cover_y), cover_sq)
        # إطار حول الصورة
        draw.rounded_rectangle(
            [cover_x - 2, cover_y - 2, cover_x + cover_size + 2, cover_y + cover_size + 2],
            radius=24, outline=(*color, 180), width=2
        )
    else:
        # مربع placeholder لو مفيش صورة
        draw.rounded_rectangle(
            [cover_x, cover_y, cover_x + cover_size, cover_y + cover_size],
            radius=22, fill=(20, 25, 60)
        )
        note_font = load_font(FONT_BOLD, 80)
        draw.text(
            (cover_x + cover_size // 2, cover_y + cover_size // 2),
            "♪", font=note_font, fill=(*color, 150), anchor="mm"
        )

    # ===== النصوص =====
    title_font  = load_font(FONT_BOLD, 52)
    sub_font    = load_font(FONT, 28)
    small_font  = load_font(FONT, 24)
    badge_font  = load_font(FONT_BOLD, 22)

    text_x = 400

    # اسم الأغنية
    clean_title = title[:30] + ("..." if len(title) > 30 else "")
    draw.text((text_x, 195), clean_title, font=title_font, fill=(255, 255, 255))

    # اسم القناة/المجموعة
    draw.text((text_x, 265), f"🎵  {ctitle}", font=sub_font, fill=(200, 200, 220))

    # اسم الطالب
    if requester:
        draw.text((text_x, 310), f"👤  {requester}", font=sub_font, fill=(180, 180, 210))

    # الوقت الحالي بتوقيت القاهرة
    cairo_time = get_cairo_time()
    draw.text((text_x, 355), f"🕐  {cairo_time}", font=sub_font, fill=(160, 160, 200))

    # خط فاصل
    draw.line([(text_x, 400), (1200, 400)], fill=(*color, 80), width=1)

    # ===== إيكوالايزر =====
    draw_equalizer(draw, color, x_start=text_x, y_base=510, count=26, bar_w=9, gap=6)

    # ===== شريط التقدم =====
    draw_progress(draw, color, x=text_x, y=545, width=780)

    # وقت البداية والنهاية
    draw.text((text_x, 562), "0:00", font=small_font, fill=(*color, 200))
    if duration and int(duration) > 0:
        mins, secs = divmod(int(duration), 60)
        hrs, mins = divmod(mins, 60)
        dur_str = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"
    else:
        dur_str = "--:--"
    draw.text((1185, 562), dur_str, font=small_font, fill=(*color, 200), anchor="ra")

    # ===== watermark =====
    wm_font = load_font(FONT_BOLD, 36)
    draw.text((1210, 698), "TALASHNY", font=wm_font, fill=(255, 255, 255, 45), anchor="ra")

    # ===== حفظ =====
    out = f"search/final{userid}.png"
    bg.convert("RGB").save(out, quality=95)
    return out
