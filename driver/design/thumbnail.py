import os
import random
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720

FONT_BOLD = "driver/source/medium.ttf"
FONT = "driver/source/regular.ttf"


def fonts():
    try:
        big = ImageFont.truetype(FONT_BOLD, 64)
        med = ImageFont.truetype(FONT, 36)
        small = ImageFont.truetype(FONT, 24)
    except:
        big = med = small = ImageFont.load_default()
    return big, med, small


def circle(img, size):
    img = img.resize((size, size)).convert("RGBA")

    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, size, size), fill=255)

    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0), mask)

    return out


def neon_glow(base, cx, cy, r):
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)

    d.ellipse(
        [cx-r-50, cy-r-50, cx+r+50, cy+r+50],
        fill=(130, 90, 255, 120)
    )

    glow = glow.filter(ImageFilter.GaussianBlur(90))
    base.alpha_composite(glow)


def spectrum(draw):

    center = W // 2
    base = H - 170

    for i in range(-45, 45):

        x = center + i * 12
        h = random.randint(10, 120)

        draw.rounded_rectangle(
            [x, base - h, x + 8, base],
            radius=3,
            fill=(255, 255, 255, 200)
        )


def progress(draw):

    bar_w = 500
    bar_x = W // 2 - bar_w // 2
    bar_y = H - 90

    draw.rectangle(
        [bar_x, bar_y, bar_x + bar_w, bar_y + 6],
        fill=(255,255,255,60)
    )

    prog = int(bar_w * 0.45)

    draw.rectangle(
        [bar_x, bar_y, bar_x + prog, bar_y + 6],
        fill=(255,255,255,200)
    )

    draw.ellipse(
        [bar_x + prog - 6, bar_y - 4,
         bar_x + prog + 6, bar_y + 10],
        fill=(255,255,255)
    )


def watermark(draw):

    try:
        font = ImageFont.truetype(FONT_BOLD, 130)
    except:
        font = ImageFont.load_default()

    draw.text(
        (W//2 - 350, H//2 + 150),
        "TALASHNY",
        font=font,
        fill=(255,255,255,20)
    )


async def thumb(thumbnail, title, userid, ctitle):

    os.makedirs("search", exist_ok=True)
    path = f"search/thumb{userid}.png"

    cover = None

    if thumbnail:
        try:
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
        bg = bg.filter(ImageFilter.GaussianBlur(35))

    else:

        bg = Image.new("RGBA", (W, H), (15, 15, 30))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 170))
    bg.alpha_composite(overlay)

    draw = ImageDraw.Draw(bg)

    cx = W // 2
    cy = H // 2 - 80

    neon_glow(bg, cx, cy, 150)

    if cover:

        cover_circle = circle(cover, 300)
        bg.paste(cover_circle, (cx - 150, cy - 150), cover_circle)

    big, med, small = fonts()

    title = title[:32]

    draw.text(
        (W//2 - 320, H//2 + 120),
        title,
        font=big,
        fill=(255,255,255)
    )

    draw.text(
        (W//2 - 320, H//2 + 200),
        f"Playing on: {ctitle}",
        font=med,
        fill=(210,210,210)
    )

    spectrum(draw)

    progress(draw)

    watermark(draw)

    out = f"search/final{userid}.png"

    bg.convert("RGB").save(out, quality=95)

    return out
