"""الذكاء الاصطناعي — دردشة + تحليل منتج"""
import streamlit as st
st.set_page_config(page_title="الذكاء الاصطناعي | مهووس", page_icon="🤖", layout="wide")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from styles import apply; apply(st)

from utils.ai_helper import chat, analyze_product
try:
    from config import GEMINI_API_KEYS
except Exception:
    GEMINI_API_KEYS = []

st.title("🤖 الذكاء الاصطناعي")

if not GEMINI_API_KEYS:
    st.error("❌ لا توجد مفاتيح Gemini — أضفها في Secrets")
    st.code('GEMINI_API_KEYS = \'["AIzaSy..."]\' ', language="toml")
    st.stop()

st.success(f"✅ {len(GEMINI_API_KEYS)} مفتاح Gemini نشط")

tab1, tab2 = st.tabs(["💬 دردشة", "🔬 تحليل منتج"])

# ── دردشة حرة ──
with tab1:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(msg["u"])
        with st.chat_message("assistant"):
            st.write(msg["a"])

    user_msg = st.chat_input("اسأل عن أي منتج أو استراتيجية تسعير...")
    if user_msg:
        with st.chat_message("user"):
            st.write(user_msg)
        with st.chat_message("assistant"):
            with st.spinner("🤖 جاري التفكير..."):
                reply = chat(user_msg, st.session_state.chat_history)
                st.write(reply)
        st.session_state.chat_history.append({"u": user_msg, "a": reply})

    if st.button("🗑️ مسح المحادثة"):
        st.session_state.chat_history = []
        st.rerun()

# ── تحليل منتج محدد ──
with tab2:
    c1, c2, c3 = st.columns(3)
    product_name = c1.text_input("اسم المنتج", placeholder="Dior Sauvage EDP 100ml")
    our_price    = c2.number_input("سعرنا", min_value=0.0, value=0.0, step=1.0)
    comp_price   = c3.number_input("سعر المنافس", min_value=0.0, value=0.0, step=1.0)
    comp_name    = st.text_input("اسم المنافس", value="المنافس")
    page_type    = st.selectbox("نوع التحليل", ["higher","lower","review","missing","chat"])

    if st.button("🤖 تحليل", type="primary", disabled=not product_name):
        with st.spinner("🤖 جاري التحليل..."):
            result = analyze_product(product_name, our_price, comp_price, comp_name, page_type)
            st.markdown(result)
