import os
import random
import aiofiles
import aiohttp
from urllib.parse import unquote
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_REGULAR = "driver/source/regular.ttf"
FONT_MEDIUM = "driver/source/medium.ttf"

W, H = 1280, 720


def _get_fonts():
    try:
        f_big = ImageFont.truetype(FONT_MEDIUM, 60)
        f_med = ImageFont.truetype(FONT_REGULAR, 36)
        f_small = ImageFont.truetype(FONT_REGULAR, 26)
    except:
        f_big = f_med = f_small = ImageFont.load_default()
    return f_big, f_med, f_small


def _clean_url(url):
    if not url:
        return ""
    if "%" in url:
        url = unquote(url)
    return url if url.startswith("http") else ""


def _gradient_bg():
    base = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(base)

    for y in range(H):
        r = int(15 + y * 0.03)
        g = int(15 + y * 0.02)
        b = int(35 + y * 0.05)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    return base


def _draw_particles(draw):
    for _ in range(120):
        x = random.randint(0, W)
        y = random.randint(0, H)
        size = random.choice([1, 2, 3])

        draw.ellipse(
            [x, y, x + size, y + size],
            fill=(255, 255, 255, random.randint(80, 200))
        )


def make_circle(img, size):
    img = img.resize((size, size)).convert("RGBA")

    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, size, size), fill=255)

    circle = Image.new("RGBA", (size, size))
    circle.paste(img, (0, 0), mask)

    return circle


def _cover_glow(img, cx, cy):
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)

    gd.ellipse(
        [cx - 170, cy - 170, cx + 170, cy + 170],
        fill=(108, 92, 231, 90)
    )

    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img.alpha_composite(glow)


def _draw_vinyl(draw, cx, cy):
    r_out = 220

    draw.ellipse(
        [cx - r_out, cy - r_out, cx + r_out, cy + r_out],
        fill=(20, 20, 40),
        outline=(255, 255, 255, 30),
        width=2
    )

    for r in [200, 180, 160, 140]:
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=(255, 255, 255, 15)
        )


def _shadow_text(draw, pos, text, font):
    x, y = pos
    draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 160))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 240))


def _draw_waveform(draw):
    base_y = H - 120
    bar_w = 6
    gap = 4

    for i in range(120):
        x = 60 + i * (bar_w + gap)
        h = random.randint(10, 60)

        draw.rounded_rectangle(
            [x, base_y - h, x + bar_w, base_y],
            radius=3,
            fill=(108, 92, 231, random.randint(120, 200))
        )


def _draw_progress(draw, progress=0.4):
    bar_x = 60
    bar_y = H - 60
    bar_w = W - 120
    bar_h = 6

    draw.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
        radius=4,
        fill=(255, 255, 255, 40)
    )

    prog_w = int(bar_w * progress)

    draw.rounded_rectangle(
        [bar_x, bar_y, bar_x + prog_w, bar_y + bar_h],
        radius=4,
        fill=(108, 92, 231, 230)
    )

    px = bar_x + prog_w

    draw.ellipse(
        [px - 8, bar_y - 5, px + 8, bar_y + bar_h + 5],
        fill=(139, 124, 246)
    )


async def thumb(thumbnail, title, userid, ctitle):

    thumbnail = _clean_url(thumbnail)
    os.makedirs("search", exist_ok=True)

    thumb_path = f"search/thumb{userid}.png"

    cover_img = None

    if thumbnail:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumbnail) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await resp.read())

                        cover_img = Image.open(thumb_path).convert("RGBA")
        except:
            pass

    img = _gradient_bg()
    draw = ImageDraw.Draw(img, "RGBA")

    _draw_particles(draw)

    cx, cy = 360, 330

    _cover_glow(img, cx, cy)

    draw = ImageDraw.Draw(img, "RGBA")

    _draw_vinyl(draw, cx, cy)

    if cover_img:
        size = 240
        circle = make_circle(cover_img, size)

        img.paste(
            circle,
            (cx - size // 2, cy - size // 2),
            circle
        )

        draw.ellipse(
            [cx - size // 2 - 6, cy - size // 2 - 6,
             cx + size // 2 + 6, cy + size // 2 + 6],
            outline=(108, 92, 231, 200),
            width=5
        )

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)

    ov.rectangle(
        [0, H - 180, W, H],
        fill=(10, 10, 20, 210)
    )

    img.alpha_composite(overlay)

    draw = ImageDraw.Draw(img, "RGBA")

    f_big, f_med, f_small = _get_fonts()

    title = title[:30] + ("..." if len(title) > 30 else "")
    group = ctitle[:20]

    _shadow_text(draw, (650, H - 150), title, f_big)

    draw.text(
        (650, H - 80),
        f"Playing on: {group}",
        font=f_med,
        fill=(180, 170, 240, 220)
    )

    _draw_waveform(draw)

    _draw_progress(draw)

    out = f"search/final{userid}.png"

    img.convert("RGB").save(out, quality=95)

    try:
        os.remove(thumb_path)
    except:
        pass

    return out
