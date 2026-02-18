"""
styles.py — التنسيقات المشتركة لكل صفحات مهووس
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans Arabic', sans-serif !important;
    direction: rtl;
}
.stButton button {
    border-radius: 8px;
    font-weight: 600;
}
.stDataFrame { direction: rtl; }
[data-testid="stSidebar"] { background: #0f172a; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
div[data-testid="metric-container"] {
    background: #1e293b;
    border-radius: 10px;
    padding: 12px;
}
/* تحسين الجداول */
.stDataFrame table { direction: rtl; }
/* تحسين الأزرار */
.stDownloadButton button { border-radius: 8px; font-weight: 600; }
</style>
"""

def apply(st):
    """تطبيق CSS على الصفحة الحالية"""
    st.markdown(CSS, unsafe_allow_html=True)
