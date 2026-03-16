import os
import random
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720

FONT_BOLD = "driver/source/medium.ttf"
FONT = "driver/source/regular.ttf"


def load_fonts():
    try:
        big = ImageFont.truetype(FONT_BOLD, 60)
        med = ImageFont.truetype(FONT, 32)
        small = ImageFont.truetype(FONT, 22)
    except:
        big = med = small = ImageFont.load_default()
    return big, med, small


def make_circle(img, size):
    img = img.resize((size, size)).convert("RGBA")

    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, size, size), fill=255)

    circle = Image.new("RGBA", (size, size))
    circle.paste(img, (0, 0), mask)

    return circle


def draw_spectrum(draw):

    base = H - 160
    center = W // 2

    for i in range(-40, 40):

        x = center + i * 12
        h = random.randint(20, 100)

        draw.rectangle(
            [x, base - h, x + 6, base],
            fill=(255, 255, 255, 180)
        )


def draw_progress(draw):

    bar_w = 500
    bar_x = W // 2 - bar_w // 2
    bar_y = H - 90

    draw.rectangle(
        [bar_x, bar_y, bar_x + bar_w, bar_y + 6],
        fill=(255, 255, 255, 60)
    )

    progress = int(bar_w * 0.4)

    draw.rectangle(
        [bar_x, bar_y, bar_x + progress, bar_y + 6],
        fill=(255, 255, 255, 220)
    )

    draw.ellipse(
        [bar_x + progress - 6, bar_y - 5,
         bar_x + progress + 6, bar_y + 11],
        fill=(255, 255, 255)
    )


def watermark(draw):

    try:
        font = ImageFont.truetype(FONT_BOLD, 100)
    except:
        font = ImageFont.load_default()

    draw.text(
        (W//2 - 300, H//2 + 150),
        "TALASHNY",
        font=font,
        fill=(255, 255, 255, 18)
    )


async def thumb(thumbnail, title, userid, ctitle):

    os.makedirs("search", exist_ok=True)

    path = f"search/thumb{userid}.png"

    cover = None

    if thumbnail:

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumbnail) as resp:

                    if resp.status == 200:

                        async with aiofiles.open(path, "wb") as f:
                            await f.write(await resp.read())

                        cover = Image.open(path).convert("RGBA")

        except:
            pass

    if cover:

        bg = cover.resize((W, H))
        bg = bg.filter(ImageFilter.GaussianBlur(30))

    else:

        bg = Image.new("RGBA", (W, H), (20, 20, 40))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 160))
    bg.alpha_composite(overlay)

    draw = ImageDraw.Draw(bg)

    big, med, small = load_fonts()

    # مكان الصورة
    cx = W // 2
    cy = 250

    if cover:

        circle = make_circle(cover, 260)

        bg.paste(circle, (cx - 130, cy - 130), circle)

        draw.ellipse(
            [cx - 140, cy - 140, cx + 140, cy + 140],
            outline=(255, 255, 255, 120),
            width=4
        )

    title = title[:32]

    draw.text(
        (W//2 - 320, 380),
        title,
        font=big,
        fill=(255, 255, 255)
    )

    draw.text(
        (W//2 - 320, 450),
        f"Playing on: {ctitle}",
        font=med,
        fill=(200, 200, 200)
    )

    draw_spectrum(draw)

    draw_progress(draw)

    watermark(draw)

    out = f"search/final{userid}.png"

    bg.convert("RGB").save(out, quality=95)

    return out
