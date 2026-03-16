import os
import random
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720

FONT = "driver/source/regular.ttf"
FONT_BOLD = "driver/source/medium.ttf"


def fonts():
    try:
        big = ImageFont.truetype(FONT_BOLD, 48)
        med = ImageFont.truetype(FONT, 30)
        small = ImageFont.truetype(FONT, 22)
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


def waveform(draw):
    base = H - 120
    for i in range(70):

        x = 250 + i * 12
        h = random.randint(10, 50)

        draw.rectangle(
            [x, base - h, x + 6, base],
            fill=(255, 255, 255, 120)
        )


def watermark(draw):

    try:
        font = ImageFont.truetype(FONT_BOLD, 32)
    except:
        font = ImageFont.load_default()

    draw.text(
        (W - 220, H - 40),
        "TALASHNY",
        font=font,
        fill=(255, 255, 255, 40)
    )


async def thumb(thumbnail, title, userid, ctitle):

    os.makedirs("search", exist_ok=True)

    thumb_path = f"search/thumb{userid}.png"

    cover = None

    if thumbnail:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(thumbnail) as r:
                    if r.status == 200:

                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await r.read())

                        cover = Image.open(thumb_path).convert("RGBA")
        except:
            pass

    if cover:

        bg = cover.resize((W, H))
        bg = bg.filter(ImageFilter.GaussianBlur(25))

    else:

        bg = Image.new("RGBA", (W, H), (20, 20, 35))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 150))
    bg.alpha_composite(overlay)

    draw = ImageDraw.Draw(bg)

    card_w = 520
    card_h = 340

    card_x = (W - card_w) // 2
    card_y = (H - card_h) // 2

    card = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 40))

    card = card.filter(ImageFilter.GaussianBlur(1))

    bg.paste(card, (card_x, card_y), card)

    draw = ImageDraw.Draw(bg)

    big, med, small = fonts()

    if cover:

        cover_circle = circle(cover, 160)

        cx = W // 2 - 80
        cy = card_y + 30

        bg.paste(cover_circle, (cx, cy), cover_circle)

    title = title[:28]

    draw.text(
        (W // 2 - 200, card_y + 210),
        title,
        font=big,
        fill=(255, 255, 255)
    )

    draw.text(
        (W // 2 - 200, card_y + 270),
        f"Playing on: {ctitle}",
        font=med,
        fill=(200, 200, 200)
    )

    bar_x = W // 2 - 200
    bar_y = card_y + 310
    bar_w = 400

    draw.rectangle(
        [bar_x, bar_y, bar_x + bar_w, bar_y + 6],
        fill=(255, 255, 255, 80)
    )

    prog = int(bar_w * 0.45)

    draw.rectangle(
        [bar_x, bar_y, bar_x + prog, bar_y + 6],
        fill=(255, 255, 255, 200)
    )

    waveform(draw)

    watermark(draw)

    out = f"search/final{userid}.png"

    bg.convert("RGB").save(out, quality=95)

    return out
