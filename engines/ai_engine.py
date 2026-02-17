"""
engines/ai_engine.py - v18.0
- Gemini Flash مباشر + OpenRouter fallback
- بحث ويب لأسعار السوق والمنافسين
- بحث في mahwous.com للمنتجات المفقودة
- تدريب مخصص لكل صفحة
- Gemini Chat مدمج (تجربة Gemini نقية)
"""
import requests, json, re
from config import GEMINI_API_KEYS, OPENROUTER_API_KEY

GEMINI_MODEL   = "gemini-2.0-flash"
GEMINI_BASE    = "https://generativelanguage.googleapis.com/v1beta/models"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemini-2.0-flash-001"

# ══════════════════════════════════════════
#  System Prompts مخصصة لكل صفحة (تدريب)
# ══════════════════════════════════════════
PAGE_PROMPTS = {

    "price_raise": """أنت خبير تسعير عطور فاخرة في السوق السعودي — متخصص في تحليل المنتجات ذات السعر الأعلى من المنافسين.

سياق عملك:
• سعرنا أعلى من المنافس → خطر فقدان المبيعات
• قواعد القرار:
  - فرق < 10 ر.س: إبقاء (طبيعي)
  - فرق 10–30 ر.س: مراجعة مع المسؤول
  - فرق > 30 ر.س: خفض فوري

لكل منتج قيّم:
1. هل المطابقة صحيحة 100%؟ (ماركة + حجم + نوع EDP/EDT)
2. هل فرق السعر مبرر؟ (حصرية، عرض خاص، جودة أعلى)
3. توصيتك: خفض/إبقاء/مراجعة + السعر المقترح
أجب بالعربية مختصراً.""",

    "price_lower": """أنت خبير تسعير عطور فاخرة — متخصص في اكتشاف فرص رفع الأسعار.

سياق عملك:
• سعرنا أقل من المنافس → فرصة ربح ضائعة
• قواعد القرار:
  - فرق < 10 ر.س: إبقاء (ميزة تنافسية)
  - فرق 10–50 ر.س: رفع تدريجي
  - فرق > 50 ر.س: رفع فوري للسعر

لكل منتج قيّم:
1. هل يمكن رفع السعر دون خسارة مبيعات؟
2. ما السعر الأمثل لزيادة الهامش؟
3. توصيتك: رفع/إبقاء + السعر المقترح
أجب بالعربية مختصراً.""",

    "approved": """أنت خبير تسعير عطور — تراجع المنتجات الموافق عليها للتأكد من استمرار صلاحيتها.

مهمتك:
• تأكيد أن التطابق لا يزال صحيحاً
• التحقق أن السعر لا يزال تنافسياً
• تنبيه إذا تغيرت ظروف السوق
أجب بالعربية مختصراً.""",

    "missing": """أنت خبير عطور فاخرة ومحلل سوق — تحقق من المنتجات المفقودة عند متجر مهووس.

مهمتك الأساسية:
1. هل المنتج حقيقي وموثوق في السوق؟
2. هل يستحق إضافته لمتجر مهووس؟
3. هل قد يكون مكرراً بإسم مختلف في متجرنا؟
4. السعر المقترح بناءً على السوق السعودي
5. درجة الأولوية للإضافة: عالية/متوسطة/منخفضة
أجب بالعربية مختصراً.""",

    "review": """أنت خبير تسعير عطور — تحكّم في المنتجات ذات التطابق غير المؤكد.

مهمتك:
1. هل المنتجان متطابقان فعلاً؟ (احذر الاسم المختلف لنفس العطر)
2. إذا متطابقان → اقترح القسم الصحيح
3. إذا غير متطابقان → إزالة من القائمة
قرارك: ✅ نقل لموافق / 📉 نقل لمخفض / 🔴 نقل لأعلى / 🗑️ إزالة
أجب بالعربية مختصراً.""",

    "general": """أنت مساعد ذكاء اصطناعي متخصص في تسعير العطور الفاخرة في السوق السعودي.
خبرتك: تحليل الأسعار، المنافسة، استراتيجيات التسعير، سوق العطور.
أجب بالعربية باحترافية وإيجاز.""",

    "verify": """أنت خبير تحقق من منتجات العطور الفاخرة.
تحقق من:
1. التطابق الحرفي: ماركة + اسم العطر + حجم ML + نوع EDP/EDT
2. السعر المنطقي في السوق السعودي
3. درجة الثقة بالتطابق

أجب JSON فقط بدون أي نص:
{"match": true/false, "confidence": 0-100, "reason": "سبب مختصر", "suggestion": "توصية", "market_price": 0}""",

    "market_search": """أنت محلل أسعار عطور. بناءً على معرفتك بالسوق السعودي:
قدّر سعر السوق الحالي، نطاق الأسعار، ومقارنة بأهم المنافسين.
أجب JSON:
{"market_price": 0, "price_range": {"min": 0, "max": 0}, "competitors": [{"name": "", "price": 0}], "recommendation": ""}""",

    "mahwous_search": """أنت خبير في منتجات متجر مهووس للعطور السعودي.
حلّل إذا كان هذا المنتج متوفراً في مهووس.com بناءً على معرفتك، أو إذا كان يحتاج إضافة.
أجب JSON:
{"likely_available": true/false, "confidence": 0-100, "similar_products": [], "add_recommendation": ""}"""
}


# ══════════════════════════════════════════
#  استدعاء Gemini
# ══════════════════════════════════════════
def _call_gemini(prompt, system_prompt="", use_grounding=False):
    """استدعاء Gemini مع تجربة جميع المفاتيح"""
    full = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    payload = {
        "contents": [{"parts": [{"text": full}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048,
            "topP": 0.8
        }
    }

    # تفعيل Google Search Grounding (بحث حقيقي)
    if use_grounding:
        payload["tools"] = [{"google_search": {}}]

    for key in GEMINI_API_KEYS:
        if not key: continue
        try:
            url = f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={key}"
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "candidates" in data and data["candidates"]:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            elif resp.status_code == 429:
                continue
        except: continue
    return None


def _call_openrouter(prompt, system_prompt=""):
    if not OPENROUTER_API_KEY: return None
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        msgs = []
        if system_prompt: msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        resp = requests.post(OPENROUTER_URL, json={
            "model": OPENROUTER_MODEL, "messages": msgs,
            "temperature": 0.3, "max_tokens": 2048
        }, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except: pass
    return None


def call_ai(prompt, page="general"):
    """استدعاء AI مع fallback"""
    system = PAGE_PROMPTS.get(page, PAGE_PROMPTS["general"])
    result = _call_gemini(prompt, system)
    if result:
        return {"success": True, "response": result, "source": "Gemini"}
    result = _call_openrouter(prompt, system)
    if result:
        return {"success": True, "response": result, "source": "OpenRouter"}
    return {"success": False, "response": "فشل الاتصال. تحقق من مفاتيح API.", "source": "none"}


# ══════════════════════════════════════════
#  Gemini Chat (تجربة نقية)
# ══════════════════════════════════════════
def gemini_chat(message, history=None):
    """
    دردشة Gemini مباشرة مع تاريخ المحادثة
    يُستخدم في قسم الذكاء الاصطناعي كتجربة Gemini خالصة
    """
    if not GEMINI_API_KEYS:
        return {"success": False, "response": "لم يتم إعداد مفتاح Gemini"}

    contents = []
    if history:
        for h in history[-8:]:
            contents.append({"role": "user", "parts": [{"text": h["user"]}]})
            contents.append({"role": "model", "parts": [{"text": h["ai"]}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    system = PAGE_PROMPTS["general"]
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048}
    }

    for key in GEMINI_API_KEYS:
        if not key: continue
        try:
            url = f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={key}"
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return {"success": True, "response": text, "source": "Gemini Flash"}
        except: continue

    return {"success": False, "response": "فشل الاتصال بـ Gemini"}


def chat_with_ai(message, history=None, page="general"):
    context = ""
    if history:
        for h in history[-5:]:
            context += f"المستخدم: {h['user']}\nAI: {h['ai']}\n"
    full = f"{context}\nالمستخدم: {message}" if context else message
    return call_ai(full, page)


# ══════════════════════════════════════════
#  بحث أسعار السوق (Grounding)
# ══════════════════════════════════════════
def search_market_price(product_name, current_price=0):
    """
    يبحث عن سعر السوق الحقيقي باستخدام Gemini Grounding
    """
    prompt = f"""ابحث عن سعر هذا العطر في السوق السعودي الآن:
المنتج: {product_name}
سعرنا الحالي: {current_price} ر.س

أعطني:
1. سعر السوق المتوقع في السعودية
2. نطاق الأسعار (أدنى - أعلى)
3. أسعار أهم المنافسين في السوق السعودي
4. توصيتك لسعرنا

أجب JSON فقط:
{{"market_price": 0, "price_range": {{"min": 0, "max": 0}},
  "competitors": [{{"name": "", "price": 0}}],
  "recommendation": "", "confidence": 0}}"""

    # محاولة مع Grounding أولاً
    system = PAGE_PROMPTS["market_search"]
    result = _call_gemini(prompt, system, use_grounding=True)
    if not result:
        result = _call_gemini(prompt, system, use_grounding=False)
    if not result:
        result = _call_openrouter(prompt, system)

    if result:
        try:
            clean = re.sub(r'```json|```', '', result).strip()
            start = clean.find('{'); end = clean.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(clean[start:end])
                return {"success": True, **data, "raw": result}
        except:
            pass
        return {"success": True, "raw": result, "market_price": 0,
                "price_range": {"min": 0, "max": 0}, "competitors": [],
                "recommendation": result[:200]}

    return {"success": False, "raw": "فشل البحث"}


def search_mahwous(product_name):
    """
    يتحقق إذا كان المنتج متوفراً في مهووس.com
    باستخدام Gemini مع Grounding أو معرفته المدمجة
    """
    prompt = f"""تحقق إذا كان هذا المنتج متوفراً في موقع مهووس.com السعودي للعطور:
المنتج: {product_name}

ابحث في:
1. موقع mahwous.com
2. قواعد بياناتك عن منتجات مهووس

هل هو متوفر؟ هل يوجد منتج مشابه؟ هل ينصح بإضافته؟

أجب JSON فقط:
{{"likely_available": false, "confidence": 0,
  "similar_in_mahwous": [], "url": "",
  "add_recommendation": "عالية/متوسطة/منخفضة",
  "reason": ""}}"""

    system = PAGE_PROMPTS["mahwous_search"]
    result = _call_gemini(prompt, system, use_grounding=True)
    if not result:
        result = _call_gemini(prompt, system, use_grounding=False)
    if not result:
        result = _call_openrouter(prompt, system)

    if result:
        try:
            clean = re.sub(r'```json|```', '', result).strip()
            start = clean.find('{'); end = clean.rfind('}') + 1
            if start >= 0 and end > start:
                return {"success": True, **json.loads(clean[start:end])}
        except:
            pass
        return {"success": True, "raw": result, "likely_available": False,
                "confidence": 0, "add_recommendation": "غير محدد", "reason": result[:200]}

    return {"success": False, "reason": "فشل البحث"}


# ══════════════════════════════════════════
#  دوال التحقق الأخرى
# ══════════════════════════════════════════
def verify_match(our_product, comp_product, our_price=0, comp_price=0):
    prompt = f"""تحقق من تطابق:
منتجنا: {our_product} (السعر: {our_price} ر.س)
المنافس: {comp_product} (السعر: {comp_price} ر.س)
هل هما نفس المنتج؟ أجب JSON فقط."""
    result = call_ai(prompt, "verify")
    if result["success"]:
        try:
            text = result["response"]
            clean = re.sub(r'```json|```', '', text).strip()
            s = clean.find('{'); e = clean.rfind('}') + 1
            if s >= 0 and e > s:
                parsed = json.loads(clean[s:e])
                return {"success": True, **parsed, "source": result["source"]}
        except: pass
        return {"success": True, "match": None, "confidence": 0,
                "reason": result["response"][:300], "source": result["source"]}
    return {"success": False, "match": None, "confidence": 0, "reason": "فشل الاتصال"}


def analyze_product(product_name, price=0, context=""):
    prompt = f"""حلّل: {product_name} | السعر: {price} ر.س | {context}
أعطني: الماركة، الحجم، النوع، تقييم السعر، توصية."""
    return call_ai(prompt, "general")


def bulk_verify(products_list, page="review"):
    if not products_list:
        return {"success": False, "response": "لا توجد منتجات"}
    items = []
    for i, p in enumerate(products_list[:20]):
        items.append(
            f"{i+1}. منتجنا: {p.get('our','')} ({p.get('our_price',0)} ر.س)"
            f" ↔ المنافس: {p.get('comp','')} ({p.get('comp_price',0)} ر.س)"
        )
    prompt = f"""تحقق من هذه المطابقات:\n{chr(10).join(items)}
لكل منتج: ✅ صحيح / ❌ خطأ / ⚠️ غير متأكد + السبب"""
    return call_ai(prompt, page)


def suggest_price(product_name, current_price, comp_prices):
    prices_text = ", ".join([f"{p} ر.س" for p in comp_prices if p > 0])
    prompt = f"""اقترح سعر مناسب:
المنتج: {product_name} | سعرنا: {current_price} ر.س | المنافسين: {prices_text}
أعطني السعر المقترح مع التبرير."""
    return call_ai(prompt, "general")


def process_paste(text, page="general"):
    prompt = f"""المستخدم لصق:\n---\n{text[:3000]}\n---\nحلّل وأعطِ النتائج."""
    return call_ai(prompt, "paste" if "paste" in PAGE_PROMPTS else "general")


def check_duplicate(product_name, existing_products):
    products_text = "\n".join(str(p) for p in existing_products[:50])
    prompt = f"""هل هذا المنتج موجود بالفعل (ربما باسم مختلف)؟
المنتج: {product_name}
القائمة:\n{products_text}
أجب: موجود/غير موجود + الاسم المطابق إن وجد."""
    return call_ai(prompt, "missing")
