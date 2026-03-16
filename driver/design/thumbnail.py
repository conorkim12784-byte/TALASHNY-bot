import os
import aiohttp
import aiofiles
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from collections import Counter

W, H = 1280, 720

FONT = "driver/source/regular.ttf"
FONT_BOLD = "driver/source/medium.ttf"


def load_fonts():
    try:
        title = ImageFont.truetype(FONT_BOLD, 55)
        text = ImageFont.truetype(FONT, 30)
    except:
        title = text = ImageFont.load_default()
    return title, text


def circle(img, size):

    img = img.resize((size, size)).convert("RGBA")

    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, size, size), fill=255)

    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0), mask)

    return out


def dominant_color(img):

    img = img.resize((100, 100))
    pixels = list(img.getdata())

    r, g, b = Counter(pixels).most_common(1)[0][0]

    return (r, g, b)


def glow(base, color):

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)

    d.ellipse(
        [50, 150, 450, 550],
        fill=(*color, 120)
    )

    glow = glow.filter(ImageFilter.GaussianBlur(120))
    base.alpha_composite(glow)


def spectrum(draw, color):

    start = 250
    base = 560

    for i in range(70):

        x = start + i * 12
        h = random.randint(20, 90)

        draw.rectangle(
            [x, base - h, x + 7, base],
            fill=(*color, 200)
        )


def progress(draw, color):

    bar_x = 250
    bar_y = 620
    bar_w = 780

    draw.rectangle(
        [bar_x, bar_y, bar_x + bar_w, bar_y + 6],
        fill=(255,255,255,60)
    )

    p = int(bar_w * 0.45)

    draw.rectangle(
        [bar_x, bar_y, bar_x + p, bar_y + 6],
        fill=color
    )

    draw.ellipse(
        [bar_x+p-6, bar_y-5, bar_x+p+6, bar_y+11],
        fill=color
    )


def watermark(draw):

    try:
        font = ImageFont.truetype(FONT_BOLD, 42)
    except:
        font = ImageFont.load_default()

    draw.text(
        (1060, 680),
        "TALASHNY",
        font=font,
        fill=(255,255,255,60)
    )


async def thumb(thumbnail, title, userid, ctitle):

    os.makedirs("search", exist_ok=True)

    path = f"search/{userid}.png"

    cover = None

    # التحقق من صحة الـ URL قبل الطلب
    is_valid_url = (
        thumbnail
        and isinstance(thumbnail, str)
        and thumbnail.startswith(("http://", "https://"))
    )

    try:

        if not is_valid_url:
            raise ValueError(f"Invalid thumbnail URL: {thumbnail!r}")

        async with aiohttp.ClientSession() as s:
            async with s.get(thumbnail) as r:

                if r.status == 200:

                    async with aiofiles.open(path, "wb") as f:
                        await f.write(await r.read())

                    cover = Image.open(path).convert("RGBA")

    except:
        pass

    if cover:

        bg = cover.resize((W, H))
        bg = bg.filter(ImageFilter.GaussianBlur(40))

        color = dominant_color(cover)

    else:

        bg = Image.new("RGBA", (W, H), (20,20,40))
        color = (120,120,255)

    overlay = Image.new("RGBA", (W, H), (0,0,0,180))
    bg.alpha_composite(overlay)

    glow(bg, color)

    draw = ImageDraw.Draw(bg)

    title_font, text_font = load_fonts()

    if cover:

        cover_circle = circle(cover, 300)
        bg.paste(cover_circle, (80, 200), cover_circle)

    draw.text(
        (450,260),
        title[:32],
        font=title_font,
        fill=(255,255,255)
    )

    draw.text(
        (450,340),
        f"Playing on: {ctitle}",
        font=text_font,
        fill=(220,220,220)
    )

    spectrum(draw, color)

    progress(draw, color)

    watermark(draw)

    out = f"search/final{userid}.png"

    bg.convert("RGB").save(out, quality=95)

    return out
