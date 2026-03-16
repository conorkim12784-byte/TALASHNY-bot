import os
import random
import aiofiles
import aiohttp
from urllib.parse import unquote
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_REGULAR = "driver/source/regular.ttf"
FONT_MEDIUM  = "driver/source/medium.ttf"
W, H = 1280, 720


def _get_fonts():
    try:
        f_big   = ImageFont.truetype(FONT_MEDIUM,  64)
        f_med   = ImageFont.truetype(FONT_REGULAR, 38)
        f_small = ImageFont.truetype(FONT_REGULAR, 28)
    except Exception:
        f_big = f_med = f_small = ImageFont.load_default()
    return f_big, f_med, f_small


def _clean_url(url: str) -> str:
    if not url:
        return ""
    if "%" in url:
        url = unquote(url)
    return url if url.startswith("http") else ""


def _draw_stars(draw, count=60):
    """رسم نجوم عشوائية في الخلفية"""
    rng = random.Random(42)
    for _ in range(count):
        x = rng.randint(0, W)
        y = rng.randint(0, H - 150)
        r = rng.choice([1, 1, 1, 2, 2])
        alpha = rng.randint(80, 200)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(255, 255, 255, alpha))


def _draw_glows(img):
    """رسم توهجات ملونة في الخلفية"""
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    # توهج بنفسجي يسار
    gd.ellipse([-100, 200, 400, 650], fill=(108, 92, 231, 60))
    # توهج أزرق يمين
    gd.ellipse([900, -50, 1380, 450], fill=(10, 26, 80, 80))
    # توهج أسفل
    gd.ellipse([300, 500, 980, 820], fill=(26, 26, 64, 50))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=80))
    img.alpha_composite(glow)


def _draw_vinyl(draw, cx, cy, cover):
    """رسم شكل الفينيل الدائري"""
    # الدائرة الخارجية الكبيرة
    r_out = 220
    draw.ellipse([cx-r_out, cy-r_out, cx+r_out, cy+r_out],
                 fill=(20, 20, 50, 255), outline=(255, 255, 255, 20), width=1)
    # حلقات الفينيل
    for r, alpha in [(210, 15), (190, 20), (170, 15), (150, 10)]:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r],
                     fill=None, outline=(255, 255, 255, alpha), width=1)
    # صورة الغلاف في المنتصف
    if cover:
        try:
            r_cover = 120
            cover_sq = cover.resize((r_cover*2, r_cover*2))
            mask = Image.new("L", (r_cover*2, r_cover*2), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, r_cover*2, r_cover*2], fill=255)
            cover_sq.putalpha(mask)
            img_temp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            img_temp.paste(cover_sq, (cx - r_cover, cy - r_cover), mask)
            return img_temp
        except Exception:
            pass
    # نوتة موسيقية لو مفيش غلاف
    r_inner = 110
    draw.ellipse([cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner],
                 fill=(42, 42, 85, 255))
    r_tiny = 18
    draw.ellipse([cx-r_tiny, cy-r_tiny, cx+r_tiny, cy+r_tiny],
                 fill=(30, 30, 60, 255))
    # حلقة دائرية متقطعة
    r_dash = 216
    for i in range(0, 360, 15):
        import math
        x1 = cx + r_dash * math.cos(math.radians(i))
        y1 = cy + r_dash * math.sin(math.radians(i))
        x2 = cx + r_dash * math.cos(math.radians(i + 8))
        y2 = cy + r_dash * math.sin(math.radians(i + 8))
        draw.line([x1, y1, x2, y2], fill=(108, 92, 231, 120), width=2)
    return None


def _draw_progress_bar(draw, progress=0.4):
    """رسم بار التشغيل"""
    bar_x, bar_y = 60, H - 68
    bar_w = W - 120
    bar_h = 5
    # الخلفية
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                             radius=3, fill=(255, 255, 255, 30))
    # التقدم
    prog_w = int(bar_w * progress)
    draw.rounded_rectangle([bar_x, bar_y, bar_x + prog_w, bar_y + bar_h],
                             radius=3, fill=(108, 92, 231, 230))
    # نقطة التشغيل
    px = bar_x + prog_w
    draw.ellipse([px-7, bar_y-4, px+7, bar_y+bar_h+4],
                 fill=(139, 124, 246, 255))


async def thumb(thumbnail, title, userid, ctitle):
    thumbnail = _clean_url(thumbnail)
    thumb_path = f"search/thumb{userid}.png"
    cover_img = None

    os.makedirs("search", exist_ok=True)

    # حاول تحميل صورة الغلاف
    if thumbnail:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumbnail, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await resp.read())
                        cover_img = Image.open(thumb_path).convert("RGBA")
        except Exception:
            pass

    # أنشئ الكانفاس
    img = Image.new("RGBA", (W, H), (13, 13, 26, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    # طبقة التوهجات
    _draw_glows(img)
    draw = ImageDraw.Draw(img, "RGBA")

    # النجوم
    _draw_stars(draw)

    # الفينيل (يسار الوسط)
    cx, cy = 360, 330
    cover_layer = _draw_vinyl(draw, cx, cy, cover_img)
    if cover_layer:
        img.alpha_composite(cover_layer)
        draw = ImageDraw.Draw(img, "RGBA")

    # شريط سفلي شبه شفاف
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay, "RGBA")
    ov_draw.rectangle([0, H - 160, W, H], fill=(9, 9, 21, 200))
    img.alpha_composite(overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    # النصوص
    f_big, f_med, f_small = _get_fonts()

    # اسم الأغنية
    title_text = title[:28] + ("..." if len(title) > 28 else "")
    draw.text((700, H - 145), title_text, font=f_big, fill=(255, 255, 255, 240))

    # اسم الجروب
    group_text = f"Playing on: {ctitle[:18]}"
    draw.text((700, H - 75), group_text, font=f_med, fill=(168, 157, 232, 200))

    # بار التشغيل
    _draw_progress_bar(draw)

    # حفظ
    out_path = f"search/final{userid}.png"
    img.convert("RGB").save(out_path, quality=95)

    # تنظيف
    for p in [thumb_path, f"search/temp{userid}.png"]:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

    return out_path
