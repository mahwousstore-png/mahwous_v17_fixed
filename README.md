# مهووس v20 - Final Release 🚀

## الملفات المطلوبة

### ✅ المجلدات:
- `utils/` - 4 ملفات
- `engines/` - 2 ملفات

### ✅ الملفات الجذرية:
- `app.py`
- `config.py`
- `styles.py`
- `requirements.txt`

## الرفع على Streamlit Cloud

1. ارفع **كل** الملفات والمجلدات
2. تأكد من وجود `utils/__init__.py`
3. تأكد من وجود `engines/__init__.py`
4. في Streamlit Cloud Settings → Secrets:
   ```toml
   GEMINI_API_KEYS = '["YOUR_KEY_HERE"]'
   ```

## التحقق من البنية:
```
mahwous_v20/
├── app.py
├── config.py
├── styles.py
├── requirements.txt
├── utils/
│   ├── __init__.py
│   ├── make_helper.py
│   ├── helpers.py
│   └── db_manager.py
└── engines/
    ├── __init__.py
    ├── engine.py
    └── ai_engine.py
```
