# driver/nowplaying.py — تخزين مين طلب الأغنية الحالية
# ملف مستقل عشان نتجنب circular imports

current_requester: dict = {}
