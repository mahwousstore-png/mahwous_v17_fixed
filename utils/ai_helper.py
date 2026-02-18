"""
utils/ai_helper.py — Gemini للتحليل في صفحات النتائج
"""
import requests, json, re, time
try:
    from config import GEMINI_API_KEYS
except Exception:
    GEMINI_API_KEYS = []

_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

_PROMPTS = {
    "higher": "خبير تسعير عطور. سعرنا أعلى من المنافس. قيّم هل الفرق مبرر، واقترح سعراً مثالياً. أجب بالعربية بإيجاز.",
    "lower":  "خبير تسعير عطور. سعرنا أقل من المنافس — فرصة رفع. اقترح سعراً أعلى يحافظ على التنافسية. أجب بالعربية بإيجاز.",
    "review": "خبير تسعير عطور. تحقق من صحة مطابقة المنتجين واتخذ قراراً: موافق/أعلى/أقل/إزالة. أجب بالعربية.",
    "missing":"خبير عطور. قيّم جدوى إضافة هذا المنتج لمتجر مهووس (أولوية: عالية/متوسطة/منخفضة + سبب). أجب بالعربية.",
    "chat":   "أنت مساعد متخصص في تسعير العطور الفاخرة للسوق السعودي. أجب بالعربية بدقة واحترافية.",
}


def _call(prompt, page="chat"):
    sys_p = _PROMPTS.get(page, _PROMPTS["chat"])
    full  = f"{sys_p}\n\n{prompt}"
    payload = {
        "contents": [{"parts": [{"text": full}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024, "topP": 0.9},
    }
    for key in GEMINI_API_KEYS:
        if not key: continue
        try:
            r = requests.post(f"{_URL}?key={key}", json=payload, timeout=30)
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            elif r.status_code == 429:
                time.sleep(1)
        except Exception:
            continue
    return None


def analyze_product(product, our_price, comp_price, comp_name, page="higher"):
    """تحليل منتج واحد"""
    diff = our_price - comp_price
    prompt = (f"المنتج: «{product}»\n"
              f"سعرنا: {our_price:.0f} ر.س\n"
              f"سعر {comp_name}: {comp_price:.0f} ر.س\n"
              f"الفرق: {diff:+.0f} ر.س ({diff/comp_price*100:+.1f}%)" if comp_price > 0
              else f"المنتج: «{product}» | سعر المنافس: {comp_price:.0f} ر.س")
    result = _call(prompt, page)
    return result or "❌ فشل الاتصال بـ Gemini"


def bulk_analyze(items, page="higher"):
    """تحليل مجموعة منتجات دفعة واحدة"""
    if not items: return "لا توجد منتجات"
    lines = "\n".join(
        f"{i+1}. {it.get('المنتج','')} | سعرنا: {it.get('السعر',0):.0f} | "
        f"منافس: {it.get('سعر_المنافس',it.get('سعر المنافس',0)):.0f} | "
        f"فرق: {it.get('الفرق',0):+.0f}ر.س"
        for i, it in enumerate(items[:20])
    )
    result = _call(f"حلّل هذه المنتجات وأعطِ توصية موجزة لكل منها:\n{lines}", page)
    return result or "❌ فشل الاتصال بـ Gemini"


def chat(message, history=None):
    """دردشة حرة"""
    ctx = ""
    if history:
        ctx = "\n".join(f"المستخدم: {h['u']}\nAI: {h['a']}" for h in history[-6:])
        ctx += "\n\n"
    result = _call(ctx + f"المستخدم: {message}", "chat")
    return result or "❌ فشل الاتصال بـ Gemini"
