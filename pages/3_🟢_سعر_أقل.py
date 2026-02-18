"""سعر أقل — فرصة لرفع السعر"""
import streamlit as st
st.set_page_config(page_title="سعر أقل | مهووس", page_icon="🟢", layout="wide")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from styles import apply; apply(st)
from utils.results_page import show_results_page

show_results_page("🟢 سعر أقل — فرصة رفع السعر", "أقل", "lower", "update")
