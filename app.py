"""
app.py - مهووس v20 Final
✅ دمج: لوحة التحكم + رفع الملفات → صفحة واحدة
✅ دمج: Make + إعدادات + سجل → صفحة واحدة
✅ عداد تقدم مباشر
✅ كل الأقسام: أعلى، أقل، موافق، مراجعة، مفقودة، AI
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import time
import threading

from config import *
from styles import get_styles
from engines.engine import (read_file, run_full_analysis, find_missing_products,
                             extract_brand, extract_size, extract_type, is_sample)
from engines.ai_engine import (call_ai, gemini_chat, verify_match,
                                search_market_price, check_duplicate,
                                fetch_fragrantica_info, generate_mahwous_description)
from utils.helpers import (apply_filters, get_filter_options, export_to_excel,
                            safe_float, format_price, format_diff)
from utils.make_helper import (send_price_updates, send_new_products,
                                send_single_product, verify_webhook_connection)
from utils.db_manager import (init_db, log_event, log_decision,
                               get_events, get_decisions)

# ══════════════════════════════════════════════
#  إعداد الصفحة
# ══════════════════════════════════════════════
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(get_styles(), unsafe_allow_html=True)
init_db()

# Session State
_defaults = {
    "results": None,
    "missing_df": None,
    "analysis_df": None,
    "chat_history": [],
    "job_running": False,
    "our_mapping": {},
    "comp_mappings": {}
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════
#  دوال مساعدة
# ══════════════════════════════════════════════
def show_column_selector(df, file_type, key_prefix):
    """واجهة اختيار أعمدة"""
    cols = list(df.columns)
    
    if file_type == "our":
        st.markdown("**🔧 اختر الأعمدة من ملف مهووس:**")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            product_col = st.selectbox("📦 المنتج", cols, key=f"{key_prefix}_prod")
        with c2:
            price_col = st.selectbox("💰 السعر", cols, key=f"{key_prefix}_price")
        with c3:
            # بحث تلقائي
            no_col = None
            for col in cols:
                if col.lower() in ["no", "id", "معرف", "sku"]:
                    no_col = col
                    break
            id_col = st.selectbox(
                "🔢 رقم (no)",
                cols,
                index=cols.index(no_col) if no_col else 0,
                key=f"{key_prefix}_id",
                help="⚠️ مهم لـ Make!"
            )
        
        st.caption("📊 معاينة:")
        st.dataframe(df[[product_col, price_col, id_col]].head(2), use_container_width=True)
        
        if df[id_col].notna().sum() > 0:
            st.success(f"✅ '{id_col}' → {df[id_col].notna().sum()} رقم")
        else:
            st.error(f"❌ '{id_col}' فارغ!")
        
        return {
            "المنتج": product_col,
            "السعر": price_col,
            "معرف_المنتج": id_col
        }
    else:
        st.markdown(f"**🔧 أعمدة {file_type}:**")
        c1, c2 = st.columns(2)
        with c1:
            product_col = st.selectbox("📦 المنتج", cols, key=f"{key_prefix}_prod")
        with c2:
            price_col = st.selectbox("💰 السعر", cols, key=f"{key_prefix}_price")
        
        st.caption("📊 معاينة:")
        st.dataframe(df[[product_col, price_col]].head(2), use_container_width=True)
        
        return {"المنتج": product_col, "السعر": price_col}


def render_section_table(df, section_name, key_prefix):
    """عرض جدول قسم"""
    if df is None or df.empty:
        st.info(f"لا توجد منتجات في {section_name}")
        return
    
    # فلاتر
    with st.expander("🔍 فلاتر", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        search = fc1.text_input("🔎 بحث", key=f"{key_prefix}_search")
        brand_f = fc2.selectbox(
            "🏷️ ماركة",
            ["الكل"] + sorted(df.get("الماركة", pd.Series()).dropna().unique().tolist()),
            key=f"{key_prefix}_brand"
        )
        match_min = fc3.slider("تطابق%", 0, 100, 0, key=f"{key_prefix}_match")
    
    filters = {
        "search": search,
        "brand": brand_f if brand_f != "الكل" else None,
        "match_min": match_min if match_min > 0 else None
    }
    filtered = apply_filters(df, filters)
    
    # تصدير
    ec1, ec2, ec3, ec4 = st.columns(4)
    with ec1:
        excel = export_to_excel(filtered, section_name)
        st.download_button(
            "📥 Excel",
            data=excel,
            file_name=f"{section_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{key_prefix}_excel"
        )
    with ec2:
        csv = filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            "📄 CSV",
            data=csv,
            file_name=f"{section_name}.csv",
            mime="text/csv",
            key=f"{key_prefix}_csv"
        )
    with ec3:
        if st.button(f"📤 Make ({len(filtered)})", key=f"{key_prefix}_make"):
            products = filtered.to_dict("records")
            if "مفقود" in section_name:
                result = send_new_products(products)
            else:
                result = send_price_updates(products)
            
            if result["success"]:
                st.success(result["message"])
            else:
                st.error(result["message"])
    with ec4:
        st.caption(f"{len(filtered)}/{len(df)}")
    
    # الجدول
    st.dataframe(filtered, use_container_width=True, height=400)


# ══════════════════════════════════════════════
#  الشريط الجانبي
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_TITLE}")
    st.caption(f"v20 Final")
    
    # حالة AI
    if GEMINI_API_KEYS:
        st.success(f"🤖 Gemini ✅ ({len(GEMINI_API_KEYS)})")
    else:
        st.warning("⚠️ Gemini غير متصل")
    
    st.markdown("---")
    
    # القائمة
    page = st.radio(
        "📑 الصفحات:",
        [
            "📊 التحليل",
            "🔴 سعر أعلى",
            "🟢 سعر أقل",
            "✅ موافق عليها",
            "⚠️ مراجعة",
            "🔵 مفقودة",
            "🤖 الذكاء الاصطناعي",
            "⚙️ النظام"
        ]
    )


# ══════════════════════════════════════════════
#  1. صفحة التحليل (دمج: لوحة التحكم + رفع)
# ══════════════════════════════════════════════
if page == "📊 التحليل":
    st.header("📊 التحليل والمقارنة")
    
    # ملخص سريع إذا كان هناك نتائج
    if st.session_state.results:
        r = st.session_state.results
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🔴 أعلى", len(r.get("price_raise", pd.DataFrame())))
        c2.metric("🟢 أقل", len(r.get("price_lower", pd.DataFrame())))
        c3.metric("✅ موافق", len(r.get("approved", pd.DataFrame())))
        c4.metric("⚠️ مراجعة", len(r.get("review", pd.DataFrame())))
        c5.metric("🔵 مفقود", len(r.get("missing", pd.DataFrame())))
        st.markdown("---")
    
    # رفع الملفات
    st.subheader("📂 رفع الملفات")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**1️⃣ ملف مهووس**")
        our_file = st.file_uploader(
            "Excel/CSV",
            type=["xlsx", "xls", "csv"],
            key="our_file"
        )
        
        if our_file:
            our_df, err = read_file(our_file)
            if err:
                st.error(f"❌ {err}")
            else:
                st.success(f"✅ {len(our_df)} منتج")
                our_mapping = show_column_selector(our_df, "our", "our")
                st.session_state.our_df = our_df
                st.session_state.our_mapping = our_mapping
    
    with col2:
        st.markdown("**2️⃣ ملفات المنافسين**")
        comp_files = st.file_uploader(
            "Excel/CSV",
            type=["xlsx", "xls", "csv"],
            accept_multiple_files=True,
            key="comp_files"
        )
        
        if comp_files:
            comp_dfs = {}
            for i, f in enumerate(comp_files):
                df, err = read_file(f)
                if not err:
                    st.success(f"✅ {f.name}: {len(df)}")
                    comp_mapping = show_column_selector(df, f.name, f"comp_{i}")
                    comp_dfs[f.name] = {
                        "df": df,
                        "mapping": comp_mapping
                    }
            st.session_state.comp_dfs = comp_dfs
    
    # زر التحليل
    st.markdown("---")
    
    if st.button("🚀 بدء التحليل", type="primary", use_container_width=True):
        if "our_df" not in st.session_state:
            st.error("❌ ارفع ملف مهووس!")
        elif "comp_dfs" not in st.session_state:
            st.error("❌ ارفع ملفات المنافسين!")
        else:
            # تطبيق mapping
            our_df = st.session_state.our_df.copy()
            our_map = st.session_state.our_mapping
            our_df = our_df.rename(columns={
                our_map["المنتج"]: "المنتج",
                our_map["السعر"]: "السعر",
                our_map["معرف_المنتج"]: "معرف_المنتج"
            })
            
            comp_dfs = {}
            for name, data in st.session_state.comp_dfs.items():
                df = data["df"].copy()
                m = data["mapping"]
                df = df.rename(columns={
                    m["المنتج"]: "المنتج",
                    m["السعر"]: "السعر"
                })
                comp_dfs[name] = df
            
            # عداد التقدم
            progress_bar = st.progress(0, text="⏳ جاري التحضير...")
            status_text = st.empty()
            
            total = len(our_df)
            
            def progress_callback(progress):
                pct = int(progress * 100)
                progress_bar.progress(progress, text=f"⚡ التحليل: {pct}%")
                if pct % 10 == 0:
                    processed = int(progress * total)
                    status_text.info(f"تم معالجة {processed}/{total} منتج")
            
            try:
                status_text.info("🔄 بدء التحليل...")
                progress_bar.progress(0.1, text="📊 المطابقة...")
                
                # التحليل
                results_df = run_full_analysis(
                    our_df,
                    comp_dfs,
                    progress_callback=progress_callback,
                    use_ai=True
                )
                
                progress_bar.progress(0.9, text="📋 التصنيف...")
                
                # التصنيف
                price_raise = results_df[results_df["القرار"].str.contains("أعلى", na=False)]
                price_lower = results_df[results_df["القرار"].str.contains("أقل", na=False)]
                approved = results_df[results_df["القرار"].str.contains("موافق", na=False)]
                review = results_df[results_df["القرار"].str.contains("مراجعة", na=False)]
                
                progress_bar.progress(0.95, text="🔍 المفقودة...")
                
                # المفقودة
                missing_df = find_missing_products(our_df, comp_dfs)
                
                # حفظ
                st.session_state.results = {
                    "all": results_df,
                    "price_raise": price_raise,
                    "price_lower": price_lower,
                    "approved": approved,
                    "review": review,
                    "missing": missing_df
                }
                
                progress_bar.progress(1.0, text="✅ اكتمل!")
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
                # ملخص
                st.success("✅ اكتمل التحليل!")
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("🔴 أعلى", len(price_raise))
                c2.metric("🟢 أقل", len(price_lower))
                c3.metric("✅ موافق", len(approved))
                c4.metric("⚠️ مراجعة", len(review))
                c5.metric("🔵 مفقود", len(missing_df))
                
                st.info("👉 اختر قسماً من القائمة الجانبية")
                
                log_event("analysis", "completed", f"{len(results_df)}")
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ خطأ: {str(e)}")


# ══════════════════════════════════════════════
#  2-6. أقسام النتائج
# ══════════════════════════════════════════════
elif page == "🔴 سعر أعلى":
    st.header("🔴 منتجات سعرها أعلى من المنافسين")
    if st.session_state.results:
        render_section_table(
            st.session_state.results.get("price_raise"),
            "سعر_أعلى",
            "raise"
        )
    else:
        st.info("قم بالتحليل أولاً")

elif page == "🟢 سعر أقل":
    st.header("🟢 منتجات سعرها أقل من المنافسين")
    if st.session_state.results:
        render_section_table(
            st.session_state.results.get("price_lower"),
            "سعر_أقل",
            "lower"
        )
    else:
        st.info("قم بالتحليل أولاً")

elif page == "✅ موافق عليها":
    st.header("✅ منتجات موافق عليها (فرق ≤10 ريال)")
    if st.session_state.results:
        render_section_table(
            st.session_state.results.get("approved"),
            "موافق",
            "approved"
        )
    else:
        st.info("قم بالتحليل أولاً")

elif page == "⚠️ مراجعة":
    st.header("⚠️ منتجات تحتاج مراجعة")
    if st.session_state.results:
        render_section_table(
            st.session_state.results.get("review"),
            "مراجعة",
            "review"
        )
    else:
        st.info("قم بالتحليل أولاً")

elif page == "🔵 مفقودة":
    st.header("🔵 منتجات مفقودة (عند المنافسين)")
    if st.session_state.results:
        render_section_table(
            st.session_state.results.get("missing"),
            "مفقودة",
            "missing"
        )
    else:
        st.info("قم بالتحليل أولاً")


# ══════════════════════════════════════════════
#  7. الذكاء الاصطناعي
# ══════════════════════════════════════════════
elif page == "🤖 الذكاء الاصطناعي":
    st.header("🤖 Gemini AI")
    
    if not GEMINI_API_KEYS:
        st.error("❌ Gemini غير متصل")
    else:
        st.success(f"🟢 Gemini Flash متصل ({len(GEMINI_API_KEYS)} مفتاح)")
    
    tab1, tab2 = st.tabs(["💬 دردشة", "🔍 تحقق"])
    
    # دردشة
    with tab1:
        st.markdown("**💬 دردشة Gemini:**")
        
        # عرض المحادثة
        for h in st.session_state.chat_history[-10:]:
            st.markdown(
                f'<div style="text-align:right;margin:4px 0">'
                f'<span style="background:#1a1a2e;padding:6px 12px;border-radius:8px;'
                f'color:#B8B4FF">👤 {h["user"]}</span></div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="ai-box" style="margin:4px 0">'
                f'{h["ai"]}</div>',
                unsafe_allow_html=True
            )
        
        # إدخال
        user_msg = st.text_input(
            "رسالتك:",
            key="chat_in",
            placeholder="اسأل عن المنتجات والأسعار..."
        )
        
        if st.button("📨 إرسال", key="chat_send"):
            if user_msg:
                with st.spinner("🤖"):
                    result = gemini_chat(user_msg, st.session_state.chat_history)
                
                if result["success"]:
                    st.session_state.chat_history.append({
                        "user": user_msg,
                        "ai": result["response"]
                    })
                    st.rerun()
    
    # تحقق
    with tab2:
        st.markdown("**🔍 تحقق من منتجين:**")
        c1, c2 = st.columns(2)
        p1 = c1.text_input("منتجنا:", key="v_our")
        p2 = c2.text_input("المنافس:", key="v_comp")
        c3, c4 = st.columns(2)
        pr1 = c3.number_input("سعرنا:", 0.0, key="v_p1")
        pr2 = c4.number_input("سعر المنافس:", 0.0, key="v_p2")
        
        if st.button("🔍 تحقق", key="vbtn"):
            if p1 and p2:
                with st.spinner("..."):
                    r = verify_match(p1, p2, pr1, pr2)
                
                if r["success"]:
                    col = "🟢" if r.get("match") else "🔴"
                    st.markdown(
                        f"{col} **{'متطابق' if r.get('match') else 'غير متطابق'}** — "
                        f"ثقة: **{r.get('confidence', 0)}%**"
                    )
                    st.info(r.get("reason", ""))


# ══════════════════════════════════════════════
#  8. النظام (دمج: Make + إعدادات + سجل)
# ══════════════════════════════════════════════
elif page == "⚙️ النظام":
    st.header("⚙️ إعدادات النظام")
    
    tab1, tab2, tab3 = st.tabs(["⚡ Make.com", "🔧 الإعدادات", "📜 السجل"])
    
    # Make
    with tab1:
        st.subheader("⚡ أتمتة Make.com")
        
        if st.button("🔌 اختبار الاتصال"):
            result = verify_webhook_connection()
            if result["success"]:
                st.success("✅ Make.com متصل!")
            else:
                st.error("❌ فشل الاتصال")
        
        st.markdown("---")
        
        if st.button("📤 إرسال منتج تجريبي"):
            test = {
                "معرف_المنتج": "TEST123",
                "المنتج": "Test Product",
                "السعر": 100,
                "سعر المنافس": 90,
                "الفرق": -10,
                "القرار": "🟢 سعر أقل"
            }
            result = send_price_updates([test])
            if result["success"]:
                st.success(result["message"])
            else:
                st.error(result["message"])
    
    # إعدادات
    with tab2:
        st.subheader("🔧 الإعدادات")
        st.info(f"Gemini: {len(GEMINI_API_KEYS)} مفتاح")
        st.info(f"Model: {GEMINI_MODEL}")
        st.info(f"Match: {MATCH_THRESHOLD}%")
        st.info(f"موافق: فرق ≤10 ريال")
    
    # السجل
    with tab3:
        st.subheader("📜 السجل")
        events = get_events(30)
        if events:
            df_events = pd.DataFrame(events, columns=[
                "ID", "الصفحة", "الحدث", "التفاصيل", "الوقت"
            ])
            st.dataframe(df_events, use_container_width=True)
        else:
            st.info("لا توجد أحداث")


# ══════════════════════════════════════════════
#  Footer
# ══════════════════════════════════════════════
st.markdown("---")
st.caption("🧪 مهووس v20 Final | Made with ❤️")
