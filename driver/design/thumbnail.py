import os
import aiohttp
import aiofiles
import random
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from collections import Counter

# الإعدادات الثابتة
W, H = 1280, 720
FONT_REGULAR = "driver/source/regular.ttf"
FONT_BOLD = "driver/source/medium.ttf"

# وظيفة لتحميل الخطوط مع معالجة الأخطاء
def get_font(font_path, size):
    try:
        return ImageFont.truetype(font_path, size)
    except:
        return ImageFont.load_default()

def circle(img, size):
    img = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    # إضافة حافة بيضاء حول الدائرة
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output

def get_dominant_color(img):
    img = img.copy()
    img.thumbnail((100, 100))
    pixels = list(img.getdata())
    # استبعاد الألوان القريبة جداً من الأسود أو الأبيض تماماً
    valid_pixels = [p for p in pixels if sum(p[:3]) > 100 and sum(p[:3]) < 650]
    if not valid_pixels: return (120, 120, 255)
    return Counter(valid_pixels).most_common(1)[0][0][:3]

async def thumb(thumbnail_url, title, userid, ctitle):
    os.makedirs("search", exist_ok=True)
    path = f"search/raw_{userid}.png"
    final_path = f"search/final_{userid}.png"

    # 1. تحميل الصورة بذكاء
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail_url) as resp:
            if resp.status == 200:
                content = await resp.read()
                async with aiofiles.open(path, mode="wb") as f:
                    await f.write(content)
                cover = Image.open(path).convert("RGBA")
            else:
                cover = Image.new("RGBA", (500, 500), (30, 30, 30))

    # 2. إنشاء الخلفية (Blur + Overlay)
    bg = cover.resize((W, H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(50))
    
    # طبقة تعتيم متدرجة (Gradient Overlay)
    dark_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 140))
    bg.alpha_composite(dark_overlay)

    # 3. استخراج اللون المسيطر للإضاءة
    main_color = get_dominant_color(cover)

    # 4. إضافة تأثير الزجاج (Glass Panel)
    draw = ImageDraw.Draw(bg)
    panel_shape = [50, 150, 1230, 570]
    # رسم مستطيل شفاف بخلفية ضبابية خفيفة
    draw.rounded_rectangle(panel_shape, radius=30, fill=(255, 255, 255, 20))
    draw.rounded_rectangle(panel_shape, radius=30, outline=(*main_color, 50), width=3)

    # 5. وضع الغلاف الدائري مع ظل
    cover_circ = circle(cover, 340)
    bg.paste(cover_circ, (120, 190), cover_circ)

    # 6. كتابة النصوص
    title_font = get_font(FONT_BOLD, 60)
    tag_font = get_font(FONT_REGULAR, 35)
    
    # كتابة العنوان (قص النص لو طويل جداً)
    clean_title = title[:30] + "..." if len(title) > 30 else title
    draw.text((500, 240), clean_title, font=title_font, fill=(255, 255, 255))
    
    # كتابة مكان التشغيل
    draw.text((500, 320), f"📍 On: {ctitle}", font=tag_font, fill=(*main_color, 255))

    # 7. شريط التقدم (Progress Bar) احترافي
    bar_x, bar_y, bar_w = 500, 480, 650
    # الخلفية للشريط
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 8], radius=4, fill=(255, 255, 255, 50))
    # التقدم (عشوائي للعرض أو يمكن تمريره كـ Parameter)
    p_width = int(bar_w * 0.6) 
    draw.rounded_rectangle([bar_x, bar_y, bar_x + p_width, bar_y + 8], radius=4, fill=main_color)
    draw.ellipse([bar_x + p_width - 8, bar_y - 4, bar_x + p_width + 8, bar_y + 12], fill=(255, 255, 255))

    # 8. إضافة العلامة المائية
    watermark_font = get_font(FONT_BOLD, 30)
    draw.text((1100, 660), "TALASHNY", font=watermark_font, fill=(255, 255, 255, 80))

    # 9. الحفظ النهائي
    bg.convert("RGB").save(final_path, "JPEG", quality=90, optimize=True)
    
    # تنظيف الملف المؤقت
    if os.path.exists(path): os.remove(path)
    
    return final_path
