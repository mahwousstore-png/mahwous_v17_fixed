# 🧪 نظام التسعير الذكي - مهووس v17.2

## 🚀 رفع على GitHub + Streamlit Cloud

### الخطوة 1: رفع الكود على GitHub
```bash
git init
git add .
git commit -m "🚀 نظام التسعير الذكي v17.2"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/mahwous-pricing.git
git push -u origin main
```

### الخطوة 2: نشر على Streamlit Cloud
1. اذهب لـ https://share.streamlit.io
2. New app → اختر Repository
3. Main file: `app.py`
4. اضغط **Advanced settings** → **Secrets**
5. انسخ محتوى `.streamlit/secrets.toml.template` وأضف مفاتيحك

### الخطوة 3: إضافة Secrets
```toml
GEMINI_KEY_1 = "AIza..."
OPENROUTER_KEY = ""
WEBHOOK_UPDATE_PRICES = "https://hook.eu2.make.com/..."
WEBHOOK_NEW_PRODUCTS = "https://hook.eu2.make.com/..."
```

---

## 📁 البنية الصحيحة للمشروع

```
mahwous-pricing/
├── app.py                          ← التطبيق الرئيسي
├── config.py                       ← الإعدادات
├── styles.py                       ← التصميم
├── requirements.txt                ← المتطلبات
│
├── engines/
│   ├── __init__.py                 ← مطلوب!
│   ├── engine.py                   ← محرك المطابقة
│   └── ai_engine.py                ← محرك AI
│
├── utils/
│   ├── __init__.py                 ← مطلوب!
│   ├── helpers.py                  ← دوال مساعدة
│   ├── make_helper.py              ← أتمتة Make.com
│   └── db_manager.py               ← قاعدة البيانات
│
└── .streamlit/
    ├── config.toml                 ← إعدادات Streamlit
    └── secrets.toml.template       ← قالب Secrets (لا ترفع secrets.toml!)
```

---

## ✨ المميزات v17.2

- 🔴 سعر أعلى | 🟢 سعر أقل | ✅ موافق | 🔍 مفقود | ⚠️ مراجعة
- 🤖 Gemini AI (3 مفاتيح) + OpenRouter fallback
- 📄 دعم CSV + Excel للرفع
- 📊 مقارنة بصرية VS بطاقات
- ⚡ أتمتة Make.com
- 📥 تصدير Excel متعدد الأوراق
- 📖 Pagination (25 منتج/صفحة)
- 💾 سجل SQLite للقرارات

---

## ⚠️ لا تنسَ!
- **لا** ترفع `.streamlit/secrets.toml` على GitHub
- أضف `secrets.toml` لملف `.gitignore`
- المفاتيح تُضاف فقط في Streamlit Cloud Secrets
