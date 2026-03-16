import os
import aiohttp
import aiofiles
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps, ImageStat
import random
import asyncio

# ─── Config ────────────────────────────────────────
W, H = 1280, 720
OUT_DIR = Path("premium_thumbs")
FONT_DIR = Path("fonts")  # حط فيه Poppins أو Montserrat أو SF Pro (أفضل للـ premium look)

OUT_DIR.mkdir(exist_ok=True)

FONT_BOLD   = str(FONT_DIR / "Montserrat-SemiBold.ttf")
FONT_MEDIUM = str(FONT_DIR / "Montserrat-Medium.ttf")
FONT_REG    = str(FONT_DIR / "Montserrat-Regular.ttf")

# ─── Helpers ────────────────────────────────────────
def get_font(path: str, size: int):
    try: return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()

def dominant_vibrant_color(img: Image.Image):
    img = img.convert("RGB").resize((80, 80), Image.Resampling.LANCZOS)
    stat = ImageStat.Stat(img)
    r, g, b = [int(x) for x in stat.median]
    # نضمن إن اللون مش رمادي أوي ويكون vibrant
    if max(r,g,b) - min(r,g,b) < 40:
        return (90, 140, 255)  # fallback أزرق premium
    return (r, g, b)

def glass_effect(base: Image.Image, blur_radius=25, opacity=110):
    """ Simulate glassmorphism: blur + dark overlay + border """
    blurred = base.filter(ImageFilter.GaussianBlur(blur_radius))
    overlay = Image.new("RGBA", base.size, (20, 20, 40, opacity))
    glass = Image.alpha_composite(blurred.convert("RGBA"), overlay)
    
    # subtle border glow
    border = Image.new("RGBA", base.size, (0,0,0,0))
    d = ImageDraw.Draw(border)
    d.rectangle((2,2, W-3, H-3), outline=(255,255,255,40), width=2)
    glass.alpha_composite(border)
    return glass

async def download(url: str, path: Path):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=10) as r:
                if r.status == 200:
                    async with aiofiles.open(path, "wb") as f:
                        await f.write(await r.read())
                    return True
    except:
        return False

# ─── Premium Generator ────────────────────────────────────────
async def generate_premium_thumbnail(
    thumbnail_url: str,
    song_title: str,
    artist_or_channel: str,
    user_id: str,
    progress: float = 0.68,          # 0.0 → 1.0
    style: str = "glass_dark"        # "glass_dark", "glass_light", "neon_premium"
) -> Path:
    user_id = str(user_id)
    tmp = OUT_DIR / f"tmp_{user_id}.jpg"
    out = OUT_DIR / f"premium_{user_id}.png"

    downloaded = await download(thumbnail_url, tmp)
    
    if downloaded:
        cover = Image.open(tmp).convert("RGB")
        bg = cover.resize((W, H), Image.Resampling.LANCZOS)
        accent = dominant_vibrant_color(cover)
    else:
        bg = Image.new("RGB", (W, H), (8, 8, 25))
        accent = (100, 180, 255)

    # Glassmorphism base
    bg = glass_effect(bg, blur_radius=30, opacity=125 if "dark" in style else 80)

    draw = ImageDraw.Draw(bg, "RGBA")

    # ─── Big Circular Art with shine ────────────────────────────────
    if downloaded:
        cover = Image.open(tmp).convert("RGBA")
        cover = cover.resize((420, 420), Image.Resampling.LANCZOS)
        
        mask = Image.new("L", (420, 420), 0)
        ImageDraw.Draw(mask).ellipse((0,0,420,420), fill=255)
        
        # subtle shine / bevel effect
        shine = Image.new("RGBA", (420,420), (0,0,0,0))
        sd = ImageDraw.Draw(shine)
        sd.ellipse((40,40,380,200), fill=(255,255,255,80))
        shine = shine.filter(ImageFilter.GaussianBlur(60))
        
        pos = (70, 150)
        bg.paste(cover, pos, mask)
        bg.alpha_composite(shine, pos)

        # thin glossy border
        draw.arc((68,148,492,572), 0, 360, fill=(255,255,255,90), width=3)

    # ─── Texts ────────────────────────────────────────────────
    title_f = get_font(FONT_BOLD, 72)
    artist_f = get_font(FONT_MEDIUM, 42)
    small_f = get_font(FONT_REG, 28)

    song_title = song_title.strip()[:48]
    # shadow + accent glow
    x, y = 540, 220
    draw.text((x+3, y+3), song_title, font=title_f, fill=(0,0,0,180))
    draw.text((x, y), song_title, font=title_f, fill=(255,255,255))

    artist_text = f" {artist_or_channel[:45]}"
    draw.text((x, y+110), artist_text, font=artist_f, fill=(220,220,255,230))

    # ─── Premium Progress Bar ────────────────────────────────────
    bar_x, bar_y, bar_w = 540, 420, 680
    fill_w = int(bar_w * progress)

    # background glass bar
    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w, bar_y+16), radius=8, fill=(255,255,255,35))

    # filled gradient bar
    if fill_w > 15:
        grad = Image.new("RGBA", (fill_w, 16), (0,0,0,0))
        gd = ImageDraw.Draw(grad)
        gd.rectangle((0,0,fill_w,16), fill=accent)
        # inner glow
        glow = grad.filter(ImageFilter.GaussianBlur(8))
        bg.alpha_composite(glow, (bar_x, bar_y))
        bg.alpha_composite(grad, (bar_x, bar_y))

    # knob / dot
    if fill_w > 20:
        draw.ellipse((bar_x+fill_w-24, bar_y-8, bar_x+fill_w+24, bar_y+24), fill=accent)
        draw.ellipse((bar_x+fill_w-16, bar_y-4, bar_x+fill_w+16, bar_y+20), fill=(255,255,255,160))

    # ─── Subtle flair ────────────────────────────────────────────
    if "neon" in style:
        for i in range(5):
            alpha = 50 - i*10
            draw.line((W-80-i*30, H-60, W-50, H-60-i*30), fill=(*accent, alpha), width=3)

    # watermark premium style
    draw.text((W-280, H-60), "PREMIUM • TALASHNY", font=small_f, fill=(255,255,255,100))

    bg.convert("RGB").save(out, quality=96, optimize=True)
    
    if tmp.exists():
        try: tmp.unlink()
        except: pass

    return out
