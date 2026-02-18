"""مهووس v21 — نظام التسعير الذكي | الصفحة الرئيسية"""
import streamlit as st

st.set_page_config(
    page_title="مهووس — تسعير ذكي",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state=True,
)

from styles import apply
apply(st)

try:
    from config import APP_VERSION
except Exception:
    APP_VERSION = "v21"

st.markdown(f"## 🧪 مهووس {APP_VERSION} — نظام التسعير الذكي")
st.markdown("اختر صفحة من القائمة الجانبية للبدء")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("📊 **التحليل** — ارفع ملفاتك وابدأ")
with col2:
    st.info("🔴🟢✅⚠️🔵 **النتائج** — استعرض التصنيفات")
with col3:
    st.info("⚙️ **النظام** — Make + إعدادات + AI")

if "results" in st.session_state and st.session_state.results is not None:
    df = st.session_state.results
    st.success(f"✅ يوجد تحليل محفوظ — {len(df)} منتج")
    dec = df["القرار"].value_counts() if "القرار" in df.columns else {}
    c1,c2,c3,c4,c5 = st.columns(5)
    for col, key in [
        (c1,"🔴 سعر أعلى"), (c2,"🟢 سعر أقل"),
        (c3,"✅ موافق عليها"), (c4,"⚠️ مراجعة"),
        (c5,"🔵 مفقود عند المنافس")
    ]:
        col.metric(key, dec.get(key, 0))

    from engines.engine import export_excel
    data = export_excel(df)
    st.download_button(
        "📥 تصدير كامل Excel",
        data,
        "mahwous_results.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
