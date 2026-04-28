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

FONT      = "driver/source/regular.ttf"
FONT_BOLD = "driver/source/medium.ttf"

BOT_NAME  = "TALASHNY"


def get_cairo_time() -> str:
    if CAIRO_TZ:
        now = datetime.now(CAIRO_TZ)
    else:
        from datetime import timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=2)))
    return now.strftime("%I:%M %p")


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def dominant_color(img):
    """يطلع لون مهيمن مشبع — مناسب للإستخدام كـ نيون"""
    img2 = img.resize((80, 80)).convert("RGB")
    pixels = [p for p in img2.getdata() if sum(p) > 80 and sum(p) < 720]
    if not pixels:
        return (80, 160, 255)
    r, g, b = Counter(pixels).most_common(1)[0][0]
    # تشبيع وتفتيح اللون عشان يطلع نيون
    mx = max(r, g, b) or 1
    factor = 230 / mx
    r = min(int(r * factor), 255)
    g = min(int(g * factor), 255)
    b = min(int(b * factor), 255)
    return (r, g, b)


def draw_equalizer(draw, color, x_start, y_base, count=34, bar_w=7, gap=5):
    for i in range(count):
        h = random.randint(12, 60)
        x = x_start + i * (bar_w + gap)
        alpha = random.randint(170, 240)
        draw.rectangle(
            [x, y_base - h, x + bar_w, y_base],
            fill=(*color, alpha)
        )


def draw_progress(draw, color, x, y, width, percent=0.52):
    draw.rounded_rectangle([x, y, x+width, y+5], radius=3, fill=(255,255,255,35))
    filled = int(width * percent)
    draw.rounded_rectangle([x, y, x+filled, y+5], radius=3, fill=(*color, 230))
    dot_x = x + filled
    draw.ellipse([dot_x-8, y-6, dot_x+8, y+11], fill=(255,255,255,255))


def _trim_letterbox(img):
    """يشيل الشرايط السوداء فوق وتحت (شائع في صور يوتيوب hqdefault)"""
    rgb = img.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    def row_is_black(y):
        # نعتبر السطر أسود لو متوسط الإضاءة أقل من 18
        s = 0
        for x in range(0, w, max(1, w // 40)):
            r, g, b = px[x, y]
            s += r + g + b
        return (s / (max(1, w // max(1, w // 40)) * 3)) < 18
    top = 0
    while top < h // 3 and row_is_black(top):
        top += 1
    bot = h - 1
    while bot > h * 2 // 3 and row_is_black(bot):
        bot -= 1
    if top > 2 or bot < h - 3:
        return img.crop((0, top, w, bot + 1))
    return img


def rounded_image(img, size, radius=999):
    """دائرة من المنتصف — مع إزالة الشرايط السوداء (letterbox) لو موجودة"""
    img = _trim_letterbox(img).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top  = (h - side) // 2
    img  = img.crop((left, top, left + side, top + side))
    img  = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([0, 0, size, size], fill=255)
    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0), mask)
    return out


def make_neon_background(color):
    """خلفية نيون داكنة (نفس القالب الأصلي) — بس بلون مشتق من صورة الأغنية"""
    # قاعدة داكنة جداً مع لمسة من اللون
    r, g, b = color
    # نمزج اللون مع الأسود عشان نطلع لون قاعدة داكن من نفس عيلة لون الأغنية
    base_dark = (
        max(int(r * 0.05), 4),
        max(int(g * 0.05), 6),
        max(int(b * 0.10), 14),
    )
    bg = Image.new("RGB", (W, H), base_dark)

    # طبقات glow راديالية بلون صورة الأغنية
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # دايرة كبيرة على شمال فوق
    od.ellipse([-200, -200, 700, 700], fill=(*color, 90))
    # دايرة على يمين تحت
    od.ellipse([W-500, H-500, W+200, H+200], fill=(*color, 70))
    # دايرة وسط خفيفة
    od.ellipse([W//2-300, H//2-300, W//2+300, H//2+300], fill=(*color, 35))

    overlay = overlay.filter(ImageFilter.GaussianBlur(120))

    canvas = bg.convert("RGBA")
    canvas.alpha_composite(overlay)

    # شبكة نقاط خفيفة جداً للتأثير التقني
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for y in range(0, H, 40):
        for x in range(0, W, 40):
            gd.point((x, y), fill=(255, 255, 255, 18))
    canvas.alpha_composite(grid)

    return canvas


async def thumb(thumbnail, title, userid, ctitle, requester=None, duration=0, **kwargs):

    os.makedirs("search", exist_ok=True)
    path  = f"search/{userid}.png"
    cover = None

    is_url = thumbnail and isinstance(thumbnail, str) and thumbnail.startswith(("http://","https://"))
    if is_url:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(thumbnail, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        async with aiofiles.open(path, "wb") as f:
                            await f.write(await r.read())
                        cover = Image.open(path).convert("RGBA")
        except:
            cover = None

    # اللون المهيمن (مشبع نيون)
    color = dominant_color(cover) if cover else (80, 160, 255)

    # ══════════════════════════════════════
    #  الخلفية: قالب نيون كامل بلون صورة الأغنية
    # ══════════════════════════════════════
    canvas = make_neon_background(color)
    draw = ImageDraw.Draw(canvas)

    # ══════════════════════════════════════
    #  البطاقة الرئيسية
    # ══════════════════════════════════════
    CARD_X1, CARD_Y1 = 60,  55
    CARD_X2, CARD_Y2 = 1220, 665
    CARD_R = 28

    # glow نيون كبير حوالين الكارد
    glow = Image.new("RGBA", (W, H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle([CARD_X1-10, CARD_Y1-10, CARD_X2+10, CARD_Y2+10],
                         radius=CARD_R+10, fill=(*color, 160))
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    canvas.alpha_composite(glow)

    # ظل أسود سفلي للعمق
    shadow2 = Image.new("RGBA", (W, H), (0,0,0,0))
    sd2 = ImageDraw.Draw(shadow2)
    sd2.rounded_rectangle([CARD_X1+6, CARD_Y1+12, CARD_X2+6, CARD_Y2+12],
                          radius=CARD_R, fill=(0,0,0,140))
    shadow2 = shadow2.filter(ImageFilter.GaussianBlur(16))
    canvas.alpha_composite(shadow2)

    # جسم البطاقة — داكن شفاف
    draw.rounded_rectangle([CARD_X1, CARD_Y1, CARD_X2, CARD_Y2],
                           radius=CARD_R, fill=(12, 16, 36, 235))
    # إطار نيون خارجي (سميك)
    draw.rounded_rectangle([CARD_X1, CARD_Y1, CARD_X2, CARD_Y2],
                           radius=CARD_R, outline=(*color, 255), width=3)
    # إطار نيون داخلي رفيع
    draw.rounded_rectangle([CARD_X1+6, CARD_Y1+6, CARD_X2-6, CARD_Y2-6],
                           radius=CARD_R-4, outline=(*color, 110), width=1)

    # ══════════════════════════════════════
    #  صورة الغلاف الدائرية + glow بلون الصورة
    # ══════════════════════════════════════
    CIR_SIZE  = 320
    CIR_X     = 105
    CIR_Y     = CARD_Y1 + (CARD_Y2 - CARD_Y1)//2 - CIR_SIZE//2

    # glow حول الدائرة
    cglow = Image.new("RGBA", (W, H), (0,0,0,0))
    cgd = ImageDraw.Draw(cglow)
    cgd.ellipse([CIR_X-25, CIR_Y-25, CIR_X+CIR_SIZE+25, CIR_Y+CIR_SIZE+25],
                fill=(*color, 180))
    cglow = cglow.filter(ImageFilter.GaussianBlur(20))
    canvas.alpha_composite(cglow)

    # حلقة خارجية نيون
    draw.ellipse([CIR_X-12, CIR_Y-12, CIR_X+CIR_SIZE+12, CIR_Y+CIR_SIZE+12],
                 outline=(*color, 255), width=4)
    # حلقة وسطى
    draw.ellipse([CIR_X-4, CIR_Y-4, CIR_X+CIR_SIZE+4, CIR_Y+CIR_SIZE+4],
                 outline=(*color, 160), width=1)

    if cover:
        cimg = rounded_image(cover, CIR_SIZE)
        canvas.paste(cimg, (CIR_X, CIR_Y), cimg)
    else:
        draw.ellipse([CIR_X, CIR_Y, CIR_X+CIR_SIZE, CIR_Y+CIR_SIZE],
                     fill=(18, 30, 80))

    # ══════════════════════════════════════
    #  خط فاصل عمودي
    # ══════════════════════════════════════
    SEP_X = 470
    draw.line([(SEP_X, CARD_Y1+20), (SEP_X, CARD_Y2-20)],
              fill=(*color, 120), width=1)

    # ══════════════════════════════════════
    #  المحتوى يمين
    # ══════════════════════════════════════
    TXT_X = SEP_X + 40
    TOP_Y = CARD_Y1 + 30

    # شارة NOW PLAYING
    badge_font = load_font(FONT_BOLD, 22)
    bw, bh     = 200, 36
    bx, by     = TXT_X - 5, TOP_Y + 5
    draw.rounded_rectangle([bx, by, bx+bw, by+bh],
                           radius=18, fill=(*color, 220))
    draw.text((bx + bw//2, by + bh//2), "NOW PLAYING",
              font=badge_font, fill=(255,255,255), anchor="mm")

    # عنوان الأغنية
    title_font  = load_font(FONT_BOLD, 50)
    sub_font    = load_font(FONT,      26)
    small_font  = load_font(FONT,      22)
    label_font  = load_font(FONT,      20)
    bot_font    = load_font(FONT_BOLD, 28)

    clean_title = title[:32] + ("..." if len(title) > 32 else "")
    draw.text((TXT_X, TOP_Y + 65), clean_title,
              font=title_font, fill=(255,255,255))

    # خط فاصل أفقي
    HR_Y = TOP_Y + 140
    draw.line([(TXT_X, HR_Y), (CARD_X2-40, HR_Y)],
              fill=(*color, 120), width=1)

    # نقطة + اسم القناة
    dot_y = HR_Y + 20
    draw.ellipse([TXT_X, dot_y+4, TXT_X+14, dot_y+18],
                 fill=(*color, 255))
    draw.text((TXT_X+24, dot_y), ctitle,
              font=load_font(FONT_BOLD, 26), fill=(*color, 255))

    HR2_Y = dot_y + 45
    draw.line([(TXT_X, HR2_Y), (CARD_X2-40, HR2_Y)],
              fill=(*color, 80), width=1)

    # Requested By
    req_y = HR2_Y + 14
    draw.text((TXT_X+10, req_y), "Requested By",
              font=label_font, fill=(170, 180, 210))
    req_name = requester or ctitle
    draw.text((TXT_X+10, req_y+24), req_name.upper(),
              font=load_font(FONT_BOLD, 28), fill=(220, 230, 255))

    # إيكوالايزر
    EQ_Y  = req_y + 90
    EQ_W  = CARD_X2 - TXT_X - 50
    count = 34
    bar_w = max(6, (EQ_W - count*5) // count)
    draw_equalizer(draw, color, x_start=TXT_X, y_base=EQ_Y,
                   count=count, bar_w=bar_w, gap=5)

    # شريط التقدم
    PG_Y  = EQ_Y + 18
    PG_W  = CARD_X2 - TXT_X - 50
    draw_progress(draw, color, x=TXT_X, y=PG_Y, width=PG_W, percent=0.52)

    draw.text((TXT_X, PG_Y+16), "0:00",
              font=small_font, fill=(180, 190, 220))

    if duration and int(duration) > 0:
        mins, secs = divmod(int(duration), 60)
        hrs, mins  = divmod(mins, 60)
        dur_str = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"
    else:
        dur_str = "--:--"
    draw.text((TXT_X + PG_W, PG_Y+16), dur_str,
              font=small_font, fill=(180, 190, 220), anchor="ra")

    # اسم البوت
    try:
        from config import BOT_NAME as _bn
        bname = _bn.upper()
    except:
        bname = BOT_NAME
    draw.text((CARD_X2 - 30, CARD_Y2 - 30), bname,
              font=bot_font, fill=(220, 230, 255), anchor="rd")

    out = f"search/final{userid}.png"
    canvas.convert("RGB").save(out, quality=95)
    return out


if __name__ == "__main__":
    import asyncio

    async def test():
        os.makedirs("search", exist_ok=True)
        out = await thumb(
            thumbnail="https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            title="Never Gonna Give You Up",
            userid=12345,
            ctitle="TALASHNY",
            requester="TALASHNY",
            duration=265,
        )
        print(f"Saved → {out}")

    asyncio.run(test())
