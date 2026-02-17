"""
app.py - مهووس v20 Final - مع واجهة اختيار أعمدة
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from config import *
from engines.engine import read_file, run_full_analysis, find_missing_products, export_excel
from utils.helpers import export_to_excel, safe_float
from utils.make_helper import send_price_updates, send_new_products, verify_webhook_connection
from utils.db_manager import init_db, log_event

# ══════════════════════════════════════════════
#  إعداد الصفحة
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="نظام التسعير مهووس v20",
    page_icon="🧪",
    layout="wide"
)

init_db()

# Session State
if "results" not in st.session_state:
    st.session_state.results = None
if "column_mapping" not in st.session_state:
    st.session_state.column_mapping = {}

# ══════════════════════════════════════════════
#  واجهة اختيار الأعمدة
# ══════════════════════════════════════════════
def show_column_selector(df, file_type="our"):
    """واجهة اختيار الأعمدة يدوياً"""
    st.subheader(f"🔧 تحديد الأعمدة - {file_type}")
    
    cols = list(df.columns)
    
    if file_type == "our":
        st.markdown("**اختر الأعمدة الصحيحة من ملف مهووس:**")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            product_col = st.selectbox(
                "📦 عمود المنتج",
                cols,
                key=f"{file_type}_product",
                help="العمود الذي يحتوي على اسم المنتج"
            )
        
        with c2:
            price_col = st.selectbox(
                "💰 عمود السعر",
                cols,
                key=f"{file_type}_price",
                help="العمود الذي يحتوي على سعر المنتج"
            )
        
        with c3:
            # البحث التلقائي عن "no"
            no_col_auto = None
            for col in cols:
                if col.lower() in ["no", "id", "معرف", "sku"]:
                    no_col_auto = col
                    break
            
            id_col = st.selectbox(
                "🔢 عمود رقم المنتج (no)",
                cols,
                index=cols.index(no_col_auto) if no_col_auto else 0,
                key=f"{file_type}_id",
                help="⚠️ مهم جداً لـ Make.com!"
            )
        
        # عرض عينة
        st.markdown("**📊 معاينة البيانات:**")
        sample_df = df[[product_col, price_col, id_col]].head(3)
        st.dataframe(sample_df, use_container_width=True)
        
        # تحقق من "no"
        if df[id_col].notna().sum() > 0:
            st.success(f"✅ عمود '{id_col}' يحتوي على {df[id_col].notna().sum()} رقم منتج")
        else:
            st.error(f"❌ عمود '{id_col}' فارغ! Make.com لن يعمل!")
        
        return {
            "المنتج": product_col,
            "السعر": price_col,
            "معرف_المنتج": id_col
        }
    
    else:  # competitor
        st.markdown(f"**اختر الأعمدة من {file_type}:**")
        c1, c2 = st.columns(2)
        
        with c1:
            product_col = st.selectbox(
                "📦 عمود المنتج",
                cols,
                key=f"{file_type}_product"
            )
        
        with c2:
            price_col = st.selectbox(
                "💰 عمود السعر",
                cols,
                key=f"{file_type}_price"
            )
        
        st.dataframe(df[[product_col, price_col]].head(3), use_container_width=True)
        
        return {
            "المنتج": product_col,
            "السعر": price_col
        }


# ══════════════════════════════════════════════
#  الشريط الجانبي
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🧪 نظام التسعير مهووس")
    st.caption("v20 Final")
    
    # حالة AI
    if GEMINI_API_KEYS:
        st.success(f"🤖 Gemini متصل ({len(GEMINI_API_KEYS)} مفتاح)")
    else:
        st.warning("⚠️ Gemini غير متصل")
    
    # اختبار Make
    st.markdown("---")
    st.markdown("### 🧪 اختبار Make.com")
    if st.button("🔌 اختبار الاتصال"):
        result = verify_webhook_connection()
        if result["success"]:
            st.success("✅ Make.com متصل!")
        else:
            st.error("❌ فشل الاتصال")


# ══════════════════════════════════════════════
#  الصفحة الرئيسية
# ══════════════════════════════════════════════
st.title("🧪 نظام التسعير الذكي - مهووس v20")

tab1, tab2, tab3 = st.tabs(["📂 رفع الملفات", "📊 النتائج", "📤 Make.com"])

# ═══ TAB 1: رفع الملفات ═══════════════════
with tab1:
    st.header("📂 رفع الملفات")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ ملف مهووس (متجرنا)")
        our_file = st.file_uploader(
            "ارفع ملف Excel/CSV",
            type=["xlsx", "xls", "csv"],
            key="our_file",
            help="يجب أن يحتوي على: اسم المنتج، السعر، رقم المنتج (no)"
        )
        
        if our_file:
            our_df, err = read_file(our_file)
            if err:
                st.error(f"❌ خطأ: {err}")
            else:
                st.success(f"✅ تم رفع {len(our_df)} منتج")
                
                # واجهة اختيار الأعمدة
                our_mapping = show_column_selector(our_df, "our")
                st.session_state.our_df = our_df
                st.session_state.our_mapping = our_mapping
    
    with col2:
        st.subheader("2️⃣ ملفات المنافسين")
        comp_files = st.file_uploader(
            "ارفع ملف أو عدة ملفات",
            type=["xlsx", "xls", "csv"],
            accept_multiple_files=True,
            key="comp_files"
        )
        
        if comp_files:
            comp_dfs = {}
            for i, f in enumerate(comp_files):
                df, err = read_file(f)
                if not err:
                    st.success(f"✅ {f.name}: {len(df)} منتج")
                    comp_mapping = show_column_selector(df, f"comp_{i}")
                    comp_dfs[f.name] = {
                        "df": df,
                        "mapping": comp_mapping
                    }
            
            st.session_state.comp_dfs = comp_dfs
    
    # زر التحليل
    st.markdown("---")
    if st.button("🚀 تحليل الأسعار", type="primary", use_container_width=True):
        if "our_df" not in st.session_state:
            st.error("❌ ارفع ملف مهووس أولاً!")
        elif "comp_dfs" not in st.session_state:
            st.error("❌ ارفع ملفات المنافسين!")
        else:
            with st.spinner("⏳ جاري التحليل..."):
                # تطبيق الـ mapping
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
                
                # التحليل
                results_df = run_full_analysis(our_df, comp_dfs)
                
                # التصنيف
                price_raise = results_df[results_df["القرار"].str.contains("أعلى", na=False)]
                price_lower = results_df[results_df["القرار"].str.contains("أقل", na=False)]
                approved = results_df[results_df["القرار"].str.contains("موافق", na=False)]
                review = results_df[results_df["القرار"].str.contains("مراجعة", na=False)]
                
                # المنتجات المفقودة
                missing_df = find_missing_products(our_df, comp_dfs)
                
                st.session_state.results = {
                    "all": results_df,
                    "price_raise": price_raise,
                    "price_lower": price_lower,
                    "approved": approved,
                    "review": review,
                    "missing": missing_df
                }
                
                st.success("✅ اكتمل التحليل!")
                log_event("analysis", "completed", f"{len(results_df)} منتج")

# ═══ TAB 2: النتائج ════════════════════════
with tab2:
    st.header("📊 النتائج")
    
    if st.session_state.results is None:
        st.info("ℹ️ ارفع الملفات وانقر 'تحليل الأسعار' أولاً")
    else:
        r = st.session_state.results
        
        # ملخص
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("🔴 سعر أعلى", len(r["price_raise"]))
        col2.metric("🟢 سعر أقل", len(r["price_lower"]))
        col3.metric("✅ موافق", len(r["approved"]))
        col4.metric("⚠️ مراجعة", len(r["review"]))
        col5.metric("🔵 مفقود", len(r["missing"]))
        
        # اختيار القسم
        section = st.selectbox(
            "اختر القسم:",
            ["الكل", "سعر أعلى", "سعر أقل", "موافق عليها", "مراجعة", "مفقودة"]
        )
        
        section_map = {
            "الكل": "all",
            "سعر أعلى": "price_raise",
            "سعر أقل": "price_lower",
            "موافق عليها": "approved",
            "مراجعة": "review",
            "مفقودة": "missing"
        }
        
        df_show = r[section_map[section]]
        
        if df_show is not None and not df_show.empty:
            # تصدير
            st.markdown("### 📥 تصدير")
            c1, c2 = st.columns(2)
            with c1:
                excel = export_to_excel(df_show, section)
                st.download_button(
                    "📥 تحميل Excel",
                    data=excel,
                    file_name=f"{section}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            with c2:
                csv = df_show.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    "📄 تحميل CSV",
                    data=csv,
                    file_name=f"{section}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            # عرض البيانات
            st.markdown(f"### {section} ({len(df_show)} منتج)")
            st.dataframe(df_show, use_container_width=True, height=400)
        else:
            st.info(f"لا توجد منتجات في قسم '{section}'")

# ═══ TAB 3: Make.com ════════════════════════
with tab3:
    st.header("📤 إرسال لـ Make.com")
    
    if st.session_state.results is None:
        st.info("ℹ️ قم بالتحليل أولاً")
    else:
        r = st.session_state.results
        
        st.markdown("### اختر القسم للإرسال:")
        
        send_section = st.selectbox(
            "القسم:",
            ["سعر أعلى", "سعر أقل", "موافق عليها", "مفقودة"],
            key="send_section"
        )
        
        section_map = {
            "سعر أعلى": "price_raise",
            "سعر أقل": "price_lower",
            "موافق عليها": "approved",
            "مفقودة": "missing"
        }
        
        df_send = r[section_map[send_section]]
        
        if df_send is not None and not df_send.empty:
            st.info(f"📊 {len(df_send)} منتج جاهز للإرسال")
            
            # معاينة
            with st.expander("👁️ معاينة البيانات"):
                st.dataframe(df_send.head(10))
            
            # إرسال
            if st.button(f"📤 إرسال {len(df_send)} منتج لـ Make.com", type="primary"):
                with st.spinner("📤 جاري الإرسال..."):
                    products = df_send.to_dict("records")
                    
                    if send_section == "مفقودة":
                        result = send_new_products(products)
                    else:
                        result = send_price_updates(products)
                    
                    if result["success"]:
                        st.success(result["message"])
                        log_event("make", "sent", f"{len(products)} منتج")
                    else:
                        st.error(result["message"])
        else:
            st.info(f"لا توجد منتجات في '{send_section}'")

# ══════════════════════════════════════════════
#  Footer
# ══════════════════════════════════════════════
st.markdown("---")
st.caption("🧪 نظام التسعير الذكي - مهووس v20 Final | Made with ❤️")
