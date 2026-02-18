"""النظام — Make.com + الإعدادات + السجل"""
import streamlit as st
st.set_page_config(page_title="النظام | مهووس", page_icon="⚙️", layout="wide")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from styles import apply; apply(st)

from utils.make_helper import test_connection, send_price_updates
try:
    from config import (GEMINI_API_KEYS, WEBHOOK_UPDATE_PRICES,
                        WEBHOOK_NEW_PRODUCTS, MATCH_THRESHOLD, PRICE_TOLERANCE,
                        APP_VERSION, GEMINI_MODEL)
except Exception:
    GEMINI_API_KEYS=[]; WEBHOOK_UPDATE_PRICES=""; WEBHOOK_NEW_PRODUCTS=""
    MATCH_THRESHOLD=62; PRICE_TOLERANCE=10; APP_VERSION="v21"; GEMINI_MODEL="gemini-2.0-flash"

st.title("⚙️ النظام")
st.caption(f"مهووس {APP_VERSION}")

tab1, tab2, tab3 = st.tabs(["⚡ Make.com", "🔧 الإعدادات", "📜 السجل"])

# ══ Make.com ══════════════════════════════════
with tab1:
    st.subheader("⚡ Make.com")
    c1, c2 = st.columns(2)
    c1.code(f"تحديث الأسعار:\n{WEBHOOK_UPDATE_PRICES}", language="text")
    c2.code(f"منتجات جديدة:\n{WEBHOOK_NEW_PRODUCTS}", language="text")

    if st.button("🔌 اختبار الاتصال", type="primary"):
        with st.spinner("جاري الاختبار..."):
            result = test_connection()
            if result["success"]:
                st.success("✅ Make.com متصل!")
            else:
                st.error("❌ فشل الاتصال")
            for name, ok in result.get("details", {}).items():
                st.write(f"{'✅' if ok else '❌'} {name}")

    st.divider()
    st.subheader("📤 إرسال تجريبي")
    if st.button("📤 إرسال منتج تجريبي"):
        test_product = {
            "معرف_المنتج": "TEST_001",
            "المنتج": "Dior Sauvage EDP 100ml TEST",
            "السعر": 450.0,
            "سعر_المنافس": 420.0,
            "الفرق": 30.0,
            "القرار": "🔴 سعر أعلى",
            "المنافس": "اختبار",
            "الماركة": "Dior",
            "نسبة_التطابق": 98.0,
        }
        with st.spinner("جاري الإرسال..."):
            result = send_price_updates([test_product])
            if result["success"]:
                st.success(result["message"])
            else:
                st.error(result["message"])

# ══ الإعدادات ══════════════════════════════════
with tab2:
    st.subheader("🔧 الإعدادات الحالية")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("مفاتيح Gemini", len(GEMINI_API_KEYS))
        st.metric("حد المطابقة التلقائية", f"{MATCH_THRESHOLD}%")
    with col2:
        st.metric("نطاق الموافقة", f"±{PRICE_TOLERANCE} ر.س")
        st.metric("النموذج", GEMINI_MODEL)

    st.divider()
    st.subheader("📝 إضافة Secrets في Streamlit Cloud")
    st.code("""
GEMINI_API_KEYS = '["AIzaSy...key1","AIzaSy...key2"]'
WEBHOOK_UPDATE_PRICES = "https://hook.eu2.make.com/..."
WEBHOOK_NEW_PRODUCTS  = "https://hook.eu2.make.com/..."
""", language="toml")

    st.divider()
    st.subheader("📊 إحصائيات الجلسة الحالية")
    if "results" in st.session_state and st.session_state.results is not None:
        df = st.session_state.results
        dec = df["القرار"].value_counts() if "القرار" in df.columns else {}
        c1,c2,c3 = st.columns(3)
        c1.metric("إجمالي المنتجات", len(df))
        c2.metric("🔴 تحتاج تدخل", dec.get("🔴 سعر أعلى", 0) + dec.get("⚠️ مراجعة", 0))
        c3.metric("✅ موافق عليها", dec.get("✅ موافق عليها", 0))
    else:
        st.info("لا يوجد تحليل حالي — انتقل لصفحة التحليل")

# ══ السجل ══════════════════════════════════════
with tab3:
    st.subheader("📜 سجل الأحداث")
    if "log" not in st.session_state:
        st.session_state.log = []

    if st.session_state.log:
        for entry in reversed(st.session_state.log[-50:]):
            st.text(entry)
    else:
        st.info("لا توجد أحداث مسجلة في هذه الجلسة")

    if st.session_state.log and st.button("🗑️ مسح السجل"):
        st.session_state.log = []
        st.rerun()
