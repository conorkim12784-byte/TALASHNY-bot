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

BOT_NAME  = "TALASHNY"   # يتغير من config لو عايز


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
    img2 = img.resize((80, 80)).convert("RGB")
    pixels = [p for p in img2.getdata() if sum(p) > 60]
    if not pixels:
        return (80, 140, 255)
    r, g, b = Counter(pixels).most_common(1)[0][0]
    mx = max(r, g, b) or 1
    factor = 210 / mx
    return (min(int(r*factor),255), min(int(g*factor),255), min(int(b*factor),255))


def draw_equalizer(draw, color, x_start, y_base, count=34, bar_w=7, gap=5):
    """إيكوالايزر — أعمدة بارتفاعات عشوائية"""
    for i in range(count):
        h = random.randint(12, 60)
        x = x_start + i * (bar_w + gap)
        alpha = random.randint(170, 240)
        draw.rectangle(
            [x, y_base - h, x + bar_w, y_base],
            fill=(*color, alpha)
        )


def draw_progress(draw, color, x, y, width, percent=0.52):
    # شريط خلفي
    draw.rounded_rectangle([x, y, x+width, y+5], radius=3, fill=(255,255,255,35))
    # شريط ملون
    filled = int(width * percent)
    draw.rounded_rectangle([x, y, x+filled, y+5], radius=3, fill=(*color, 230))
    # نقطة بيضاء
    dot_x = x + filled
    draw.ellipse([dot_x-8, y-6, dot_x+8, y+11], fill=(255,255,255,255))


def rounded_image(img, size, radius=999):
    """صورة دائرية"""
    img = img.resize((size, size)).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([0, 0, size, size], fill=255)
    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0), mask)
    return out


async def thumb(thumbnail, title, userid, ctitle, requester=None, duration=0, **kwargs):

    os.makedirs("search", exist_ok=True)
    path  = f"search/{userid}.png"
    cover = None

    # ── تحميل الغلاف ──
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

    # ── اللون المهيمن ──
    color = dominant_color(cover) if cover else (80, 140, 255)

    # ══════════════════════════════════════
    #  الخلفية الرئيسية — داكن navy مثل الصورة
    # ══════════════════════════════════════
    canvas = Image.new("RGBA", (W, H), (8, 10, 28))

    # glow زرقاوي خلف الدائرة على اليسار
    glow = Image.new("RGBA", (W, H), (0,0,0,0))
    gd   = ImageDraw.Draw(glow)
    gd.ellipse([-60, 80, 560, 640], fill=(30, 60, 180, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    canvas.alpha_composite(glow)

    draw = ImageDraw.Draw(canvas)

    # ══════════════════════════════════════
    #  البطاقة الرئيسية (card)
    # ══════════════════════════════════════
    CARD_X1, CARD_Y1 = 60,  55
    CARD_X2, CARD_Y2 = 1220, 665
    CARD_R = 28

    # ظل البطاقة
    shadow = Image.new("RGBA", (W, H), (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([CARD_X1+6, CARD_Y1+8, CARD_X2+6, CARD_Y2+8],
                         radius=CARD_R, fill=(0,0,0,80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    canvas.alpha_composite(shadow)

    # جسم البطاقة
    draw.rounded_rectangle([CARD_X1, CARD_Y1, CARD_X2, CARD_Y2],
                           radius=CARD_R, fill=(20, 26, 52, 210))
    # إطار البطاقة
    draw.rounded_rectangle([CARD_X1, CARD_Y1, CARD_X2, CARD_Y2],
                           radius=CARD_R, outline=(60, 80, 160, 120), width=1)

    # ══════════════════════════════════════
    #  صورة الغلاف — دائرة على اليسار
    # ══════════════════════════════════════
    CIR_SIZE  = 320
    CIR_X     = 105
    CIR_Y     = CARD_Y1 + (CARD_Y2 - CARD_Y1)//2 - CIR_SIZE//2  # مركزة عمودياً

    # حلقة خارجية
    draw.ellipse([CIR_X-12, CIR_Y-12, CIR_X+CIR_SIZE+12, CIR_Y+CIR_SIZE+12],
                 outline=(50, 80, 180, 140), width=2)
    # حلقة داخلية
    draw.ellipse([CIR_X-4, CIR_Y-4, CIR_X+CIR_SIZE+4, CIR_Y+CIR_SIZE+4],
                 outline=(*color, 100), width=1)

    if cover:
        cimg = rounded_image(cover, CIR_SIZE)
        canvas.paste(cimg, (CIR_X, CIR_Y), cimg)
    else:
        # placeholder دائري
        draw.ellipse([CIR_X, CIR_Y, CIR_X+CIR_SIZE, CIR_Y+CIR_SIZE],
                     fill=(18, 30, 80))
        # glow داخلي
        ig = Image.new("RGBA", (W, H), (0,0,0,0))
        igd = ImageDraw.Draw(ig)
        igd.ellipse([CIR_X+20, CIR_Y+20, CIR_X+CIR_SIZE-20, CIR_Y+CIR_SIZE-20],
                    fill=(*color, 60))
        ig = ig.filter(ImageFilter.GaussianBlur(30))
        canvas.alpha_composite(ig)

    # ══════════════════════════════════════
    #  خط فاصل رأسي
    # ══════════════════════════════════════
    SEP_X = 470
    draw.line([(SEP_X, CARD_Y1+20), (SEP_X, CARD_Y2-20)],
              fill=(60, 80, 160, 150), width=1)

    # ══════════════════════════════════════
    #  الجانب الأيمن — محتوى
    # ══════════════════════════════════════
    TXT_X    = SEP_X + 40
    TOP_Y    = CARD_Y1 + 30

    # شارة NOW PLAYING
    badge_font = load_font(FONT_BOLD, 22)
    bw, bh     = 200, 36
    bx, by     = TXT_X - 5, TOP_Y + 5
    draw.rounded_rectangle([bx, by, bx+bw, by+bh],
                           radius=18, fill=(*color, 200))
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

    # ── خط فاصل أفقي بعد العنوان ──
    HR_Y = TOP_Y + 140
    draw.line([(TXT_X, HR_Y), (CARD_X2-40, HR_Y)],
              fill=(60, 80, 160, 140), width=1)

    # نقطة + اسم القناة
    dot_y = HR_Y + 20
    draw.ellipse([TXT_X, dot_y+4, TXT_X+14, dot_y+18],
                 fill=(*color, 255))
    draw.text((TXT_X+24, dot_y), ctitle,
              font=load_font(FONT_BOLD, 26), fill=(*color, 255))

    # ── خط فاصل ──
    HR2_Y = dot_y + 45
    draw.line([(TXT_X, HR2_Y), (CARD_X2-40, HR2_Y)],
              fill=(60, 80, 160, 100), width=1)

    # Requested By
    req_y = HR2_Y + 14
    draw.text((TXT_X+10, req_y), "Requested By",
              font=label_font, fill=(170, 180, 210))
    req_name = requester or ctitle
    draw.text((TXT_X+10, req_y+24), req_name.upper(),
              font=load_font(FONT_BOLD, 28), fill=(220, 230, 255))

    # ══════════════════════════════════════
    #  إيكوالايزر
    # ══════════════════════════════════════
    EQ_Y  = req_y + 90
    EQ_W  = CARD_X2 - TXT_X - 50
    count = 34
    bar_w = max(6, (EQ_W - count*5) // count)
    draw_equalizer(draw, color, x_start=TXT_X, y_base=EQ_Y,
                   count=count, bar_w=bar_w, gap=5)

    # ══════════════════════════════════════
    #  شريط التقدم
    # ══════════════════════════════════════
    PG_Y  = EQ_Y + 18
    PG_W  = CARD_X2 - TXT_X - 50
    draw_progress(draw, color, x=TXT_X, y=PG_Y, width=PG_W, percent=0.52)

    # 0:00
    draw.text((TXT_X, PG_Y+16), "0:00",
              font=small_font, fill=(180, 190, 220))

    # المدة
    if duration and int(duration) > 0:
        mins, secs = divmod(int(duration), 60)
        hrs, mins  = divmod(mins, 60)
        dur_str = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"
    else:
        dur_str = "--:--"
    draw.text((TXT_X + PG_W, PG_Y+16), dur_str,
              font=small_font, fill=(180, 190, 220), anchor="ra")

    # ══════════════════════════════════════
    #  اسم البوت في أسفل اليمين
    # ══════════════════════════════════════
    try:
        from config import BOT_NAME as _bn
        bname = _bn.upper()
    except:
        bname = BOT_NAME
    draw.text((CARD_X2 - 30, CARD_Y2 - 30), bname,
              font=bot_font, fill=(220, 230, 255), anchor="rd")

    # ══════════════════════════════════════
    #  حفظ
    # ══════════════════════════════════════
    out = f"search/final{userid}.png"
    canvas.convert("RGB").save(out, quality=95)
    return out


# ── تست محلي ──
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
