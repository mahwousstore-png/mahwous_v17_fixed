"""مراجعة — يحتاج تدخل بشري"""
import streamlit as st
st.set_page_config(page_title="مراجعة | مهووس", page_icon="⚠️", layout="wide")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from styles import apply; apply(st)
from utils.results_page import show_results_page

show_results_page("⚠️ مراجعة — يحتاج تدخل بشري", "مراجعة", "review", "update")
