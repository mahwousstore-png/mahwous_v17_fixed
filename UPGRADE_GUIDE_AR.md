# دليل الترقية v19 → v20 🚀

## التعديلات المطلوبة

### 1️⃣ تحويل لصفحات منفصلة (حل مشكلة الثقل)

**قبل (v19):** Sidebar مع كل الأقسام في ملف واحد
**بعد (v20):** صفحات Streamlit منفصلة

#### البنية الجديدة:
```
mahwous_v20/
├── app.py                      # الرئيسي - ملاحة فقط
├── pages/
│   ├── 1_📊_التحليل.py         # دمج: لوحة التحكم + رفع الملفات
│   ├── 2_🔴_سعر_أعلى.py
│   ├── 3_🟢_سعر_أقل.py
│   ├── 4_✅_موافق_عليها.py
│   ├── 5_🔍_منتجات_مفقودة.py
│   ├── 6_⚠️_مراجعة.py
│   ├── 7_🤖_AI.py
│   └── 8_⚙️_النظام.py          # دمج: Make + إعدادات + سجل
```

---

### 2️⃣ إصلاح Make.com Webhooks

#### المشاكل في v19:
- ❌ لا يرسل رقم المنتج "no"
- ❌ تنسيق JSON غير متوافق مع Make

#### الحل في v20:
```python
# utils/make_helper.py - التعديلات المطلوبة

def send_price_updates(products):
    """
    إرسال تحديثات الأسعار لـ Make
    
    التنسيق الصحيح:
    {
        "products": [
            {
                "product_no": "12345",      # ✅ رقم المنتج (مهم جداً!)
                "name": "Dior Sauvage...",
                "current_price": 450.00,
                "new_price": 430.00,
                "competitor": "competitor1",
                "action": "lower",
                "reason": "سعر أعلى من المنافس"
            }
        ],
        "timestamp": "2026-02-17T20:30:00",
        "total_count": 10
    }
    """
    webhook_url = WEBHOOK_UPDATE_PRICES
    payload = {
        "products": [{
            "product_no": p.get("معرف_المنتج", p.get("no", "")),  # ✅ المفتاح
            "name": p.get("المنتج", ""),
            "current_price": float(p.get("السعر", 0)),
            "new_price": float(p.get("سعر_مقترح", p.get("سعر المنافس", 0))),
            "competitor": p.get("المنافس", ""),
            "action": _get_action(p.get("القرار", "")),
            "reason": p.get("التفسير", "")
        } for p in products],
        "timestamp": datetime.now().isoformat(),
        "total_count": len(products)
    }
    # ... بقية الكود

def send_new_products(products):
    """إرسال منتجات مفقودة لـ Make"""
    webhook_url = WEBHOOK_NEW_PRODUCTS
    payload = {
        "products": [{
            "name": p.get("منتج المنافس", ""),
            "price": float(p.get("سعر المنافس", 0)),
            "brand": p.get("الماركة", ""),
            "size": p.get("الحجم", ""),
            "type": p.get("النوع", ""),
            "competitor": p.get("المنافس", ""),
            "priority": _get_priority(p),  # عالية/متوسطة/منخفضة
            "image_url": p.get("image_url", ""),  # من Fragrantica
            "description": p.get("وصف_مهووس", "")
        } for p in products],
        "timestamp": datetime.now().isoformat(),
        "total_count": len(products)
    }
    # ... بقية الكود
```

---

### 3️⃣ قاعدة "موافق عليها" الجديدة

**قبل:** أي منتج مطابق تماماً
**بعد:** منتج مطابق + فرق السعر ≤ 10 ريال

```python
# في engine.py - تعديل _make_row()

def _make_row(...):
    # ... الكود الموجود
    
    # قاعدة القرار الجديدة
    if override:
        decision = override
    elif ai_source in ("gemini", "auto") or score >= HIGH_CONFIDENCE:
        abs_diff = abs(diff)
        if abs_diff <= 10:  # ✅ الفرق المسموح
            decision = "✅ موافق"
        elif diff > 10:
            decision = "🔴 سعر أعلى"
        else:  # diff < -10
            decision = "🟢 سعر أقل"
    else:
        decision = "⚠️ مراجعة"
    
    return {
        # ... بقية الحقول
        "القرار": decision,
        # ...
    }
```

---

### 4️⃣ الذاكرة التلقائية (حل مشكلة إعادة التحميل)

```python
# في app.py أو صفحة التحليل

import streamlit as st
from utils.state_manager import save_state, load_state

# في بداية التطبيق - تحميل تلقائي
if "results" not in st.session_state:
    saved = load_state()
    if saved:
        st.session_state.results = saved.get("results")
        st.session_state.missing = saved.get("missing")
        st.info(f"✅ تم تحميل آخر تحليل: {saved['timestamp'][:16]}")

# بعد كل تحليل - حفظ تلقائي
if results_df is not None:
    save_state({
        "results": st.session_state.results,
        "missing": st.session_state.missing,
        "our_file": our_file.name if our_file else None,
        "comp_files": [f.name for f in comp_files] if comp_files else []
    })
```

---

### 5️⃣ تحسينات الأداء

#### أ) تقسيم الصفحات يخفف الذاكرة
```python
# بدلاً من تحميل كل شيء في app.py واحد
# كل صفحة تحمل فقط ما تحتاجه

# pages/2_🔴_سعر_أعلى.py
import streamlit as st
# تحميل فقط بيانات "سعر أعلى"
df = st.session_state.results.get("price_raise")
```

#### ب) استخدام `@st.cache_data` للعمليات الثقيلة
```python
@st.cache_data(ttl=3600)
def run_full_analysis_cached(our_df, comp_dfs):
    return run_full_analysis(our_df, comp_dfs)
```

---

### 6️⃣ ترتيب الأزرار المحسّن

#### في render_pro_table:
```python
# الترتيب الجديد (من اليسار):
b1, b2, b3, b4, b5, b6 = st.columns(6)

with b1:  # 🤖 AI فوري
    st.button("🤖 تحقق")
    
with b2:  # 💹 بحث السوق
    st.button("💹 سوق")
    
with b3:  # ✅ قرارات
    st.button("✅ موافق")
    
with b4:  # ⏸️ تأجيل
    st.button("⏸️ تأجيل")
    
with b5:  # 📤 Make
    st.button("📤 Make")
    
with b6:  # 📈 تاريخ
    st.button("📈 تاريخ")
```

---

### 7️⃣ إصلاح مشكلة التداخل

#### المشكلة:
```python
# ❌ خطأ شائع - st.columns داخل st.expander داخل loop
for product in products:
    with st.expander(product):
        col1, col2 = st.columns(2)  # يسبب تداخل!
```

#### الحل:
```python
# ✅ الطريقة الصحيحة
for i, product in enumerate(products):
    col1, col2 = st.columns(2)
    with col1:
        st.write(product)
    with col2:
        if st.button("Action", key=f"btn_{i}"):  # ✅ key فريد
            # ...
```

---

## خطوات التنفيذ السريعة

### الخطوة 1: تحديث config.py
```python
# إضافة رقم المنتج كعمود مهم
PRODUCT_ID_COLUMNS = ["no", "NO", "No", "معرف", "ID", "id", "SKU", "sku"]
```

### الخطوة 2: تحديث engine.py
```python
# تعديل قاعدة "موافق" - السطر ~507
if abs_diff <= 10:
    decision = "✅ موافق"
```

### الخطوة 3: تحديث make_helper.py
```python
# إضافة "product_no" في كل payload
"product_no": p.get("معرف_المنتج", p.get("no", ""))
```

### الخطوة 4: إضافة state_manager.py
```bash
# إنشاء الملف الجديد
touch utils/state_manager.py
# ثم نسخ الكود أعلاه
```

### الخطوة 5: تحويل app.py لصفحات
```bash
# إنشاء مجلد pages
mkdir pages
# نقل الأقسام لملفات منفصلة
```

---

## الاختبار

### 1. اختبر Make.com
```python
# في app.py - زر اختبار
if st.button("🧪 اختبار Make"):
    test_product = {
        "معرف_المنتج": "TEST123",
        "المنتج": "Test Product",
        "السعر": 100,
        "سعر المنافس": 90
    }
    result = send_price_updates([test_product])
    st.write(result)
```

### 2. اختبر الذاكرة
```python
# في app.py
if st.button("🗑️ مسح الذاكرة"):
    clear_state()
    st.rerun()
```

### 3. اختبر موافق عليها
```python
# رفع ملف اختباري مع منتجات فرقها 5، 10، 15 ريال
# تحقق من التصنيف الصحيح
```

---

## الملاحظات المهمة

⚠️ **"no" ضروري:** تأكد أن عمود "no" موجود في ملف مهووس
⚠️ **الذاكرة:** الملف يُحفظ في نفس مجلد التطبيق
⚠️ **Make.com:** اختبر الـ webhooks في Make قبل الإنتاج
⚠️ **الأداء:** الصفحات المنفصلة أسرع 3-5x من الـ sidebar

---

## الدعم الفني

إذا واجهت مشاكل:
1. تحقق من logs: `streamlit run app.py --logger.level=debug`
2. اختبر كل صفحة منفصلة
3. تحقق من صحة رقم "no" في الملفات
