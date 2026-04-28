# proxies.py — إدارة قائمة بروكسيات Webshare مع Rotation + Health tracking
# ───────────────────────────────────────────────────────────────────────
# الفكرة:
#   • قائمة بروكسيات معرّفة هنا (أو عبر متغير بيئة PROXY_LIST).
#   • get_next_proxy() بيرجع أول بروكسي شغّال — لو فشل بنعلّمه ونتجاوزه مؤقتاً.
#   • get_all_proxies() بيرجع كل البروكسيات بترتيب أولوية (الشغالة الأول).
#   • mark_failed(proxy) بيعلّم بروكسي إنه فشل (cooldown 5 دقايق).
#   • mark_success(proxy) بيعيد تأهيله فوراً.
#   • iter_proxies() — generator يجرّب كل البروكسيات + None (بدون بروكسي) كـ fallback نهائي.
#
# طريقة الاستخدام في yt-dlp:
#   from proxies import iter_proxies
#   for proxy in iter_proxies():
#       opts = {..., "proxy": proxy} if proxy else {...}
#       try: ... ; mark_success(proxy); break
#       except: mark_failed(proxy); continue

from __future__ import annotations

import os
import time
import threading
from typing import Iterator, Optional

# ─────────────────────────────────────────
# قائمة البروكسيات الافتراضية (Webshare — username:password@host:port)
# عدّلها هنا أو استبدلها بـ PROXY_LIST في .env (مفصولة بفواصل)
# الصيغة: http://USER:PASS@HOST:PORT
# ─────────────────────────────────────────

_DEFAULT_PROXIES = [
    "http://ulhtlwea:ycf2e2no3dwl@31.59.20.176:6754",
    "http://ulhtlwea:ycf2e2no3dwl@198.23.239.134:6540",
    "http://ulhtlwea:ycf2e2no3dwl@45.38.107.97:6014",
    "http://ulhtlwea:ycf2e2no3dwl@107.172.163.27:6543",
    "http://ulhtlwea:ycf2e2no3dwl@198.105.121.200:6462",
    "http://ulhtlwea:ycf2e2no3dwl@216.10.27.159:6837",
    "http://ulhtlwea:ycf2e2no3dwl@142.111.67.146:5611",
    "http://ulhtlwea:ycf2e2no3dwl@191.96.254.138:6185",
    "http://ulhtlwea:ycf2e2no3dwl@31.58.9.4:6077",
    "http://ulhtlwea:ycf2e2no3dwl@104.239.107.47:5699",
]


def _load_proxies() -> list[str]:
    """يحمل البروكسيات من PROXY_LIST env (أولوية) أو من القائمة الافتراضية."""
    env_val = os.getenv("PROXY_LIST", "").strip()
    if env_val:
        # مفصولة بفواصل أو أسطر جديدة
        items = [p.strip() for p in env_val.replace("\n", ",").split(",")]
        return [p for p in items if p]
    return list(_DEFAULT_PROXIES)


_PROXIES: list[str] = _load_proxies()
_FAIL_COOLDOWN_SEC = int(os.getenv("PROXY_FAIL_COOLDOWN", "300"))  # 5 دقايق
_failed_until: dict[str, float] = {}  # proxy -> timestamp يفك عنده الحظر
_lock = threading.Lock()


def get_all_proxies() -> list[str]:
    """يرجع كل البروكسيات (صالحة + محظورة مؤقتاً)."""
    return list(_PROXIES)


def _is_failed(proxy: str) -> bool:
    until = _failed_until.get(proxy, 0)
    if until and time.time() < until:
        return True
    if until and time.time() >= until:
        _failed_until.pop(proxy, None)
    return False


def mark_failed(proxy: Optional[str]) -> None:
    """يعلّم بروكسي كـ فاشل لمدة _FAIL_COOLDOWN_SEC."""
    if not proxy:
        return
    with _lock:
        _failed_until[proxy] = time.time() + _FAIL_COOLDOWN_SEC
    print(f"[proxies] ❌ marked FAILED: {_mask(proxy)} (cooldown {_FAIL_COOLDOWN_SEC}s)")


def mark_success(proxy: Optional[str]) -> None:
    """يعيد تأهيل بروكسي فوراً عند نجاحه."""
    if not proxy:
        return
    with _lock:
        if proxy in _failed_until:
            _failed_until.pop(proxy, None)


def get_next_proxy() -> Optional[str]:
    """يرجع أول بروكسي شغّال (مش في cooldown)، أو None لو كلهم فاشلين."""
    with _lock:
        for p in _PROXIES:
            if not _is_failed(p):
                return p
    return None


def iter_proxies(include_no_proxy_fallback: bool = True) -> Iterator[Optional[str]]:
    """
    Generator يرجع البروكسيات بالترتيب: الشغّالة الأول، الفاشلة بعدها،
    وأخيراً None (يعني جرّب بدون بروكسي) لو include_no_proxy_fallback=True.
    """
    healthy = []
    cooldown = []
    with _lock:
        for p in _PROXIES:
            (cooldown if _is_failed(p) else healthy).append(p)
    for p in healthy:
        yield p
    for p in cooldown:
        yield p
    if include_no_proxy_fallback:
        yield None


def _mask(proxy: str) -> str:
    """يخفي الـ password في اللوج."""
    try:
        if "@" not in proxy:
            return proxy
        scheme_creds, host = proxy.rsplit("@", 1)
        scheme, creds = scheme_creds.split("://", 1)
        if ":" in creds:
            user, _ = creds.split(":", 1)
            return f"{scheme}://{user}:***@{host}"
    except Exception:
        pass
    return proxy


def status_report() -> str:
    """تقرير سريع لحالة البروكسيات (للتشخيص)."""
    lines = [f"Proxies loaded: {len(_PROXIES)}"]
    for p in _PROXIES:
        state = "❌ COOLDOWN" if _is_failed(p) else "✅ READY"
        lines.append(f"  {state}  {_mask(p)}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(status_report())
