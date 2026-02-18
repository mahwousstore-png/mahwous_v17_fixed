"""صفحة التحليل — رفع الملفات + تشغيل المحرك"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="التحليل | مهووس", page_icon="📊", layout="wide")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from styles import apply
apply(st)

from engines.engine import read_file, run_analysis, find_missing, best_col

st.title("📊 التحليل")

# ══ ملخص سريع إذا وجدت نتائج ════════════════
if "results" in st.session_state and st.session_state.results is not None:
    df = st.session_state.results
    dec = df["القرار"].value_counts() if "القرار" in df.columns else {}
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("🔴 سعر أعلى",   dec.get("🔴 سعر أعلى", 0))
    c2.metric("🟢 سعر أقل",    dec.get("🟢 سعر أقل", 0))
    c3.metric("✅ موافق عليها", dec.get("✅ موافق عليها", 0))
    c4.metric("⚠️ مراجعة",     dec.get("⚠️ مراجعة", 0))
    c5.metric("🔵 مفقود",       dec.get("🔵 مفقود عند المنافس", 0))
    st.divider()

# ══ رفع ملف مهووس ════════════════════════════
st.subheader("1️⃣ ملف مهووس")
our_file = st.file_uploader("ارفع ملف مهووس (CSV أو Excel)", type=["csv","xlsx","xls"], key="our_file")

our_df = None
our_name_col = our_price_col = our_id_col = None

if our_file:
    our_df, err = read_file(our_file)
    if err:
        st.error(f"❌ {err}")
        st.stop()

    cols = list(our_df.columns)
    st.success(f"✅ {len(our_df)} صف | {len(cols)} عمود")

    col1, col2, col3 = st.columns(3)
    with col1:
        our_name_col = st.selectbox("📦 عمود المنتج", cols,
            index=cols.index(best_col(our_df, ["المنتج","اسم المنتج","Product","Name","name"])))
    with col2:
        our_price_col = st.selectbox("💰 عمود السعر", cols,
            index=cols.index(best_col(our_df, ["السعر","سعر","Price","price"])))
    with col3:
        id_options = ["(بدون)"] + cols
        default_id = best_col(our_df, ["no","NO","No","معرف","ID","id","SKU","sku","الكود","رقم المنتج"])
        default_idx = id_options.index(default_id) if default_id in id_options else 0
        our_id_col_sel = st.selectbox("🔢 عمود رقم المنتج (no)", id_options, index=default_idx)
        our_id_col = our_id_col_sel if our_id_col_sel != "(بدون)" else None

    preview_cols = [c for c in [our_name_col, our_price_col, our_id_col] if c]
    st.dataframe(our_df[preview_cols].head(5), use_container_width=True)

    if our_id_col:
        non_null = our_df[our_id_col].dropna().astype(str).str.strip().str.len().gt(0).sum()
        st.caption(f"✅ عمود '{our_id_col}' — {non_null} قيمة")
    else:
        st.warning("⚠️ لم تختر عمود رقم المنتج — لن يمكن الإرسال لـ Make.com")

# ══ ملفات المنافسين ═══════════════════════════
st.subheader("2️⃣ ملفات المنافسين")
comp_files = st.file_uploader("ارفع ملفات المنافسين (1-5 ملفات)",
    type=["csv","xlsx","xls"], accept_multiple_files=True, key="comp_files")

comp_dfs = {}

if comp_files:
    for cf in comp_files[:5]:
        cdf, err = read_file(cf)
        if err:
            st.error(f"❌ {cf.name}: {err}")
            continue
        cname = st.text_input(f"اسم المنافس ({cf.name})",
                              value=cf.name.replace(".csv","").replace(".xlsx","").replace(".xls",""),
                              key=f"cname_{cf.name}")
        ccols = list(cdf.columns)
        c1, c2 = st.columns(2)
        with c1:
            cn_col = st.selectbox(f"عمود المنتج — {cname}", ccols,
                index=ccols.index(best_col(cdf, ["المنتج","اسم المنتج","Product","Name","name"])),
                key=f"cn_{cf.name}")
        with c2:
            cp_col = st.selectbox(f"عمود السعر — {cname}", ccols,
                index=ccols.index(best_col(cdf, ["السعر","سعر","Price","price"])),
                key=f"cp_{cf.name}")
        cdf = cdf.rename(columns={cn_col: "المنتج", cp_col: "السعر"})
        comp_dfs[cname] = cdf
        st.caption(f"✅ {cname}: {len(cdf)} منتج")

# ══ خيارات التحليل ════════════════════════════
st.subheader("3️⃣ خيارات")
col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    use_ai = st.toggle("🤖 استخدام Gemini للحالات الغامضة", value=True)
with col_opt2:
    st.caption("سيُستخدم Gemini فقط للمنتجات ذات نسبة تطابق 62-96%")

# ══ زر التحليل ════════════════════════════════
can_analyze = our_df is not None and len(comp_dfs) > 0
if st.button("🚀 بدء التحليل", type="primary", disabled=not can_analyze, use_container_width=True):

    rename_map = {}
    if our_name_col  and our_name_col  != "المنتج":        rename_map[our_name_col]  = "المنتج"
    if our_price_col and our_price_col != "السعر":         rename_map[our_price_col] = "السعر"
    if our_id_col    and our_id_col    != "معرف_المنتج":   rename_map[our_id_col]    = "معرف_المنتج"
    if rename_map:
        our_df = our_df.rename(columns=rename_map)

    total_products = len(our_df)
    progress_bar = st.progress(0.0)
    status_text  = st.empty()

    def on_progress(p):
        progress_bar.progress(min(p, 1.0))
        done = int(p * total_products)
        pct  = int(p * 100)
        status_text.markdown(f"⚡ **التحليل: {pct}%** — تم معالجة {done:,}/{total_products:,} منتج")

    status_text.markdown("⏳ جاري التحضير...")
    try:
        results = run_analysis(our_df, comp_dfs, progress_cb=on_progress, use_ai=use_ai)
        status_text.markdown("🔍 البحث عن المفقودة...")
        missing  = find_missing(our_df, comp_dfs)
        progress_bar.progress(1.0)
        status_text.markdown("✅ **اكتمل!**")

        st.session_state.results = results
        st.session_state.missing  = missing

        dec = results["القرار"].value_counts() if "القرار" in results.columns else {}
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("🔴 سعر أعلى",   dec.get("🔴 سعر أعلى", 0))
        c2.metric("🟢 سعر أقل",    dec.get("🟢 سعر أقل", 0))
        c3.metric("✅ موافق عليها", dec.get("✅ موافق عليها", 0))
        c4.metric("⚠️ مراجعة",     dec.get("⚠️ مراجعة", 0))
        c5.metric("🔵 مفقود",       len(missing) if missing is not None and len(missing) > 0 else 0)
        st.success("✅ انتقل للأقسام من القائمة الجانبية لعرض النتائج")

    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        import traceback
        st.code(traceback.format_exc())

elif not can_analyze and our_df is not None:
    st.info("ارفع ملف منافس واحد على الأقل")
elif not can_analyze:
    st.info("ارفع ملف مهووس وملف منافس للبدء")
