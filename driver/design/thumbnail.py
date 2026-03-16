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
FONT_DIR = Path("fonts")

OUT_DIR.mkdir(exist_ok=True)

FONT_BOLD   = str(FONT_DIR / "Montserrat-SemiBold.ttf")
FONT_MEDIUM = str(FONT_DIR / "Montserrat-Medium.ttf")
FONT_REG    = str(FONT_DIR / "Montserrat-Regular.ttf")

# ─── Helpers ────────────────────────────────────────
def get_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def dominant_vibrant_color(img: Image.Image):
    try:
        img = img.convert("RGB").resize((80, 80), Image.Resampling.LANCZOS)
        stat = ImageStat.Stat(img)
        r, g, b = [int(x) for x in stat.median]
        if max(r, g, b) - min(r, g, b) < 40:
            return (90, 140, 255)
        return (r, g, b)
    except Exception:
        return (90, 140, 255)

def glass_effect(base: Image.Image, blur_radius=25, opacity=110):
    try:
        blurred = base.filter(ImageFilter.GaussianBlur(blur_radius))
        overlay = Image.new("RGBA", base.size, (20, 20, 40, opacity))
        glass = Image.alpha_composite(blurred.convert("RGBA"), overlay)
        
        border = Image.new("RGBA", base.size, (0,0,0,0))
        d = ImageDraw.Draw(border)
        d.rectangle((2,2, W-3, H-3), outline=(255,255,255,40), width=2)
        glass.alpha_composite(border)
        return glass
    except Exception:
        return base.convert("RGBA")

async def download(url: str, path: Path):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=10) as r:
                if r.status == 200:
                    async with aiofiles.open(path, "wb") as f:
                        await f.write(await r.read())
                    return True
    except Exception:
        return False

# ─── الدالة اللي البوت بيدور عليها (اسمها thumb بالظبط) ────────────────
async def thumb(thumbnail, title, userid, ctitle, progress: float = 0.68, style: str = "glass_dark"):
    """
    توافق مع الاستدعاء القديم: thumb(thumbnail_url, song_title, userid, channel_title)
    """
    user_id = str(userid)
    tmp_path = OUT_DIR / f"tmp_{user_id}.jpg"
    output_path = OUT_DIR / f"thumb_{user_id}.png"

    try:
        downloaded = await download(thumbnail, tmp_path)
        
        if downloaded:
            cover = Image.open(tmp_path).convert("RGB")
            bg = cover.resize((W, H), Image.Resampling.LANCZOS)
            accent = dominant_vibrant_color(cover)
        else:
            bg = Image.new("RGB", (W, H), (8, 8, 25))
            accent = (100, 180, 255)

        bg = glass_effect(bg, blur_radius=30, opacity=125 if "dark" in style else 80)
        draw = ImageDraw.Draw(bg, "RGBA")

        # صورة الألبوم الدائرية + shine
        if downloaded:
            cover = Image.open(tmp_path).convert("RGBA")
            cover = cover.resize((420, 420), Image.Resampling.LANCZOS)
            
            mask = Image.new("L", (420, 420), 0)
            ImageDraw.Draw(mask).ellipse((0,0,420,420), fill=255)
            
            shine = Image.new("RGBA", (420,420), (0,0,0,0))
            sd = ImageDraw.Draw(shine)
            sd.ellipse((40,40,380,200), fill=(255,255,255,80))
            shine = shine.filter(ImageFilter.GaussianBlur(60))
            
            pos = (70, 150)
            bg.paste(cover, pos, mask)
            bg.alpha_composite(shine, pos)

            draw.arc((68,148,492,572), 0, 360, fill=(255,255,255,90), width=3)

        # النصوص
        title_f = get_font(FONT_BOLD, 72)
        artist_f = get_font(FONT_MEDIUM, 42)
        small_f = get_font(FONT_REG, 28)

        song_title = str(title).strip()[:48]
        x, y = 540, 220
        
        draw.text((x+3, y+3), song_title, font=title_f, fill=(0,0,0,180))
        draw.text((x, y), song_title, font=title_f, fill=(255,255,255))

        artist_text = f" {str(ctitle)[:45]}"
        draw.text((x, y+110), artist_text, font=artist_f, fill=(220,220,255,230))

        # Progress bar
        bar_x, bar_y, bar_w = 540, 420, 680
        fill_w = int(bar_w * max(0.0, min(1.0, progress)))

        draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w, bar_y+16), radius=8, fill=(255,255,255,35))

        if fill_w > 15:
            grad = Image.new("RGBA", (fill_w, 16), (0,0,0,0))
            gd = ImageDraw.Draw(grad)
            gd.rectangle((0,0,fill_w,16), fill=accent)
            glow = grad.filter(ImageFilter.GaussianBlur(8))
            bg.alpha_composite(glow, (bar_x, bar_y))
            bg.alpha_composite(grad, (bar_x, bar_y))

        if fill_w > 20:
            draw.ellipse((bar_x+fill_w-24, bar_y-8, bar_x+fill_w+24, bar_y+24), fill=accent)
            draw.ellipse((bar_x+fill_w-16, bar_y-4, bar_x+fill_w+16, bar_y+20), fill=(255,255,255,160))

        # Flair + watermark
        if "neon" in style:
            for i in range(5):
                alpha = 50 - i*10
                draw.line((W-80-i*30, H-60, W-50, H-60-i*30), fill=(*accent, alpha), width=3)

        draw.text((W-280, H-60), "PREMIUM • TALASHNY", font=small_f, fill=(255,255,255,100))

        bg.convert("RGB").save(output_path, quality=96, optimize=True)
        
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except:
                pass

        return str(output_path)

    except Exception as e:
        print(f"Thumbnail error for {user_id}: {e}")
        return "search/fallback.png"  # fallback عشان البوت ما يتعطلش
