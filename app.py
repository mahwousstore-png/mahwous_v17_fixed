"""
app.py — مهووس v21 | نظام مقارنة الأسعار الذكي
"""
import streamlit as st

st.set_page_config(
    page_title="مهووس — تسعير ذكي",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans Arabic', sans-serif !important; direction: rtl; }
.stButton button { border-radius: 8px; font-weight: 600; }
.stDataFrame { direction: rtl; }
[data-testid="stSidebar"] { background: #0f172a; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
div[data-testid="metric-container"] { background: #1e293b; border-radius: 10px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🧪 مهووس v21 — نظام التسعير الذكي")
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
    
    # زر تصدير سريع من الصفحة الرئيسية
    from engines.engine import export_excel
    data = export_excel(df)
    st.download_button(
        "📥 تصدير كامل Excel",
        data,
        "mahwous_results.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
