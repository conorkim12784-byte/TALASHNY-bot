import os
import aiofiles
import aiohttp
from urllib.parse import unquote
from PIL import Image, ImageDraw, ImageFont


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


def _clean_url(url: str) -> str:
    """إصلاح روابط الـ thumbnail المشفرة أو المكسورة"""
    if not url:
        return ""
    # فك URL encoding لو موجود
    if "%" in url:
        url = unquote(url)
    # تأكد إن الرابط صح
    if not url.startswith("http"):
        return ""
    return url


async def thumb(thumbnail, title, userid, ctitle):
    # إصلاح الرابط قبل أي حاجة
    thumbnail = _clean_url(thumbnail)

    # لو الرابط فاضل استخدم صورة افتراضية
    if not thumbnail:
        thumbnail = "https://i.ytimg.com/vi/default/hqdefault.jpg"

    thumb_path = f"search/thumb{userid}.png"
    fallback = "driver/source/LightBlue.png"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(thumb_path, mode="wb")
                    await f.write(await resp.read())
                    await f.close()
                else:
                    # لو فشل استخدم الصورة الاحتياطية
                    import shutil
                    shutil.copy(fallback, thumb_path)
    except Exception:
        import shutil
        shutil.copy(fallback, thumb_path)

    try:
        image1 = Image.open(thumb_path)
        image2 = Image.open("driver/source/LightBlue.png")
        image3 = changeImageSize(1280, 720, image1)
        image4 = changeImageSize(1280, 720, image2)
        image5 = image3.convert("RGBA")
        image6 = image4.convert("RGBA")
        Image.alpha_composite(image5, image6).save(f"search/temp{userid}.png")
        img = Image.open(f"search/temp{userid}.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("driver/source/regular.ttf", 50)
        font2 = ImageFont.truetype("driver/source/medium.ttf", 72)
        draw.text((25, 615), f"{title[:20]}...", fill="black", font=font2)
        draw.text((27, 543), f"Playing on {ctitle[:12]}", fill="black", font=font)
        img.save(f"search/final{userid}.png")
        os.remove(f"search/temp{userid}.png")
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
        return f"search/final{userid}.png"
    except Exception:
        # لو فشل كل حاجة رجع الصورة الاحتياطية
        return fallback
