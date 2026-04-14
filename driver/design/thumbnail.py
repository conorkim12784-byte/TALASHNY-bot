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
    img2 = img.resize((80, 80)).convert("RGB") if img else None
    if not img2:
        return (80, 140, 255)

    pixels = [p for p in img2.getdata() if sum(p) > 60]
    if not pixels:
        return (80, 140, 255)

    r, g, b = Counter(pixels).most_common(1)[0][0]
    mx = max(r, g, b) or 1
    factor = 210 / mx
    return (min(int(r*factor),255), min(int(g*factor),255), min(int(b*factor),255))


def draw_equalizer(draw, color, x_start, y_base, count=34, bar_w=7, gap=5):
    for i in range(count):
        h = random.randint(20, 50)
        x = x_start + i * (bar_w + gap)
        draw.rectangle(
            [x, y_base - h, x + bar_w, y_base],
            fill=(*color, 200)
        )


def draw_progress(draw, color, x, y, width, percent=0.52):
    draw.rounded_rectangle([x, y, x+width, y+8], radius=6, fill=(255,255,255,40))
    filled = int(width * percent)
    draw.rounded_rectangle([x, y, x+filled, y+8], radius=6, fill=(*color, 255))

    dot_x = x + filled
    draw.ellipse([dot_x-8, y-6, dot_x+8, y+12], fill=(255,255,255))


def rounded_image(img, size):
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

    color = dominant_color(cover) if cover else (80, 140, 255)

    # 🎨 Gradient Background
    canvas = Image.new("RGBA", (W, H))
    bg = ImageDraw.Draw(canvas)
    for i in range(H):
        ratio = i / H
        r = int(8 + ratio * 20)
        g = int(10 + ratio * 30)
        b = int(28 + ratio * 60)
        bg.line([(0, i), (W, i)], fill=(r, g, b))

    # Glow
    glow = Image.new("RGBA", (W, H), (0,0,0,0))
    gd   = ImageDraw.Draw(glow)
    gd.ellipse([-120, 40, 620, 700], fill=(*color, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    canvas.alpha_composite(glow)

    draw = ImageDraw.Draw(canvas)

    CARD_X1, CARD_Y1 = 60, 55
    CARD_X2, CARD_Y2 = 1220, 665
    CARD_R = 28

    shadow = Image.new("RGBA", (W, H), (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([CARD_X1+6, CARD_Y1+8, CARD_X2+6, CARD_Y2+8],
                         radius=CARD_R, fill=(0,0,0,80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(shadow)

    draw.rounded_rectangle([CARD_X1, CARD_Y1, CARD_X2, CARD_Y2],
                           radius=CARD_R, fill=(20, 26, 52, 160))
    draw.rounded_rectangle([CARD_X1, CARD_Y1, CARD_X2, CARD_Y2],
                           radius=CARD_R, outline=(60, 80, 160, 120), width=1)

    CIR_SIZE  = 320
    CIR_X     = 105
    CIR_Y     = CARD_Y1 + (CARD_Y2 - CARD_Y1)//2 - CIR_SIZE//2

    draw.ellipse([CIR_X-12, CIR_Y-12, CIR_X+CIR_SIZE+12, CIR_Y+CIR_SIZE+12],
                 outline=(50, 80, 180, 140), width=2)

    if cover:
        cimg = rounded_image(cover, CIR_SIZE)
        canvas.paste(cimg, (CIR_X, CIR_Y), cimg)
    else:
        draw.ellipse([CIR_X, CIR_Y, CIR_X+CIR_SIZE, CIR_Y+CIR_SIZE],
                     fill=(18, 30, 80))

    SEP_X = 470
    draw.line([(SEP_X, CARD_Y1+20), (SEP_X, CARD_Y2-20)],
              fill=(60, 80, 160, 150), width=1)

    TXT_X    = SEP_X + 40
    TOP_Y    = CARD_Y1 + 30

    title_font  = load_font(FONT_BOLD, 50)
    sub_font    = load_font(FONT,      26)
    small_font  = load_font(FONT,      22)

    clean_title = title[:32] + ("..." if len(title) > 32 else "")

    # Glow title
    draw.text((TXT_X+2, TOP_Y + 67), clean_title,
              font=title_font, fill=(*color, 120))

    draw.text((TXT_X, TOP_Y + 65), clean_title,
              font=title_font, fill=(255,255,255))

    draw.text((TXT_X, TOP_Y + 140), ctitle,
              font=sub_font, fill=color)

    EQ_Y  = TOP_Y + 300
    draw_equalizer(draw, color, TXT_X, EQ_Y)

    PG_Y  = EQ_Y + 20
    PG_W  = CARD_X2 - TXT_X - 50
    draw_progress(draw, color, TXT_X, PG_Y, PG_W, 0.52)

    if duration and int(duration) > 0:
        mins, secs = divmod(int(duration), 60)
        hrs, mins  = divmod(mins, 60)
        dur_str = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"
    else:
        dur_str = "--:--"

    draw.text((TXT_X, PG_Y+20), "0:00",
              font=small_font, fill=(180, 190, 220))

    draw.text((TXT_X + PG_W, PG_Y+20), dur_str,
              font=small_font, fill=(180, 190, 220), anchor="ra")

    # Grain effect
    noise = Image.effect_noise((W, H), 8).convert("L")
    noise = noise.point(lambda x: x * 0.15)
    canvas = Image.composite(canvas, Image.new("RGBA", (W,H)), noise)

    out = f"search/final{userid}.png"
    canvas.convert("RGB").save(out, quality=95)

    return out
