"""
utils/results_page.py — مكون مشترك لصفحات النتائج الخمس
v21: إصلاح خطأ color_row + إعادة الصفحة عند تغيير الفلاتر + تحسينات UI
"""
import streamlit as st
import pandas as pd
from engines.engine import export_excel

ROWS = 25


def _apply_filters(df, section):
    """فلاتر موحدة لكل الصفحات"""
    with st.expander("🔎 الفلاتر", expanded=False):
        c1, c2, c3 = st.columns(3)
        search = c1.text_input("بحث بالاسم", key=f"search_{section}")
        brands = []
        if "الماركة" in df.columns:
            brands = sorted(df["الماركة"].dropna().unique().tolist())
        brand  = c2.selectbox("الماركة", ["الكل"] + brands, key=f"brand_{section}")
        comps  = []
        if "المنافس" in df.columns:
            comps = sorted(df["المنافس"].dropna().unique().tolist())
        comp   = c3.selectbox("المنافس", ["الكل"] + comps, key=f"comp_{section}")

        diff_range = None
        if "الفرق" in df.columns and len(df) > 0:
            mn, mx = float(df["الفرق"].min()), float(df["الفرق"].max())
            if mn < mx:
                diff_range = st.slider("نطاق الفرق (ر.س)", mn, mx, (mn, mx),
                                        key=f"diff_{section}")

        sort_by = st.selectbox("ترتيب حسب", ["الفرق ↓","الفرق ↑","نسبة التطابق ↓","السعر ↓","المنتج أ→ي"],
                               key=f"sort_{section}")

    # إعادة الصفحة إلى 1 عند تغيير الفلاتر
    filter_state = (search, brand, comp, str(diff_range), sort_by)
    prev_key = f"prev_filter_{section}"
    if st.session_state.get(prev_key) != filter_state:
        st.session_state[f"page_{section}"] = 1
        st.session_state[prev_key] = filter_state

    filtered = df.copy()
    if search:
        mask = (filtered["المنتج"].astype(str).str.contains(search, case=False, na=False) |
                filtered.get("منتج_المنافس", pd.Series([""] * len(filtered))).astype(str).str.contains(search, case=False, na=False))
        filtered = filtered[mask]
    if brand != "الكل" and "الماركة" in filtered.columns:
        filtered = filtered[filtered["الماركة"] == brand]
    if comp  != "الكل" and "المنافس" in filtered.columns:
        filtered = filtered[filtered["المنافس"] == comp]
    if diff_range and "الفرق" in filtered.columns:
        filtered = filtered[(filtered["الفرق"] >= diff_range[0]) & (filtered["الفرق"] <= diff_range[1])]

    sort_map = {
        "الفرق ↓":            ("الفرق", False),
        "الفرق ↑":            ("الفرق", True),
        "نسبة التطابق ↓":     ("نسبة_التطابق", False),
        "السعر ↓":            ("السعر", False),
        "المنتج أ→ي":         ("المنتج", True),
    }
    sort_col, asc = sort_map.get(sort_by, ("الفرق", False))
    if sort_col in filtered.columns:
        filtered = filtered.sort_values(sort_col, ascending=asc)

    return filtered.reset_index(drop=True)


def _display_table(df, section):
    """عرض الجدول مع pagination — v21: إصلاح خطأ color_row"""
    total = len(df)
    pages = max(1, (total - 1) // ROWS + 1)
    page_key = f"page_{section}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    page = max(1, min(st.session_state[page_key], pages))
    st.session_state[page_key] = page

    show_cols = [c for c in [
        "المنتج","الماركة","الحجم","النوع","السعر",
        "منتج_المنافس","سعر_المنافس","الفرق","الفرق_بالنسبة",
        "نسبة_التطابق","مصدر_المطابقة","المنافس","معرف_المنتج"
    ] if c in df.columns]

    start = (page-1)*ROWS
    # ✅ FIXED: نحتفظ بالـ index متسقاً بين chunk_full و chunk_display
    chunk_full = df.iloc[start:start+ROWS].reset_index(drop=True)
    chunk_display = chunk_full[show_cols].copy() if show_cols else chunk_full.copy()

    color_map = {
        "🔴": "background-color:#fff0f0",
        "🟢": "background-color:#f0fff0",
        "✅": "background-color:#f0fff8",
        "⚠️": "background-color:#fffbf0",
        "🔵": "background-color:#f0f4ff",
    }

    def color_row(row):
        if "القرار" not in chunk_full.columns:
            return [""] * len(row)
        dec = str(chunk_full.at[row.name, "القرار"])
        for emoji, style in color_map.items():
            if emoji in dec:
                return [style] * len(row)
        return [""] * len(row)

    try:
        styled = chunk_display.style.apply(color_row, axis=1)
        st.dataframe(styled, use_container_width=True, height=min(total * 38 + 40, 650))
    except Exception:
        st.dataframe(chunk_display, use_container_width=True)

    if pages > 1:
        c1, c2, c3 = st.columns([1,3,1])
        if c1.button("◀ السابق", key=f"prev_{section}", disabled=page <= 1):
            st.session_state[page_key] = page - 1
            st.rerun()
        c2.markdown(f"<div style='text-align:center;padding:8px'>صفحة {page} من {pages} | إجمالي: {total}</div>",
                    unsafe_allow_html=True)
        if c3.button("التالي ▶", key=f"next_{section}", disabled=page >= pages):
            st.session_state[page_key] = page + 1
            st.rerun()
    else:
        st.caption(f"إجمالي: {total} منتج")
    return df


def _export_make_bar(df, section, make_type="update"):
    """شريط التصدير والإرسال — v21: تصدير مباشر + تأكيد Make"""
    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        data = export_excel(df, sheet=section[:31])
        st.download_button(
            f"📥 تصدير Excel ({len(df)})",
            data,
            f"{section}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{section}"
        )

    with c2:
        if st.button(f"📤 إرسال لـ Make ({len(df)})", key=f"make_{section}"):
            st.session_state[f"confirm_make_{section}"] = True

        if st.session_state.get(f"confirm_make_{section}"):
            st.warning(f"⚠️ سيتم إرسال **{len(df)}** منتج — متأكد؟")
            cc1, cc2 = st.columns(2)
            if cc1.button("✅ نعم", key=f"confirm_yes_{section}"):
                with st.spinner("جاري الإرسال..."):
                    from utils.make_helper import send_price_updates, send_new_products
                    records = df.to_dict("records")
                    result = send_new_products(records) if make_type == "new" else send_price_updates(records)
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
                st.session_state[f"confirm_make_{section}"] = False
            if cc2.button("❌ إلغاء", key=f"confirm_no_{section}"):
                st.session_state[f"confirm_make_{section}"] = False
                st.rerun()

    with c3:
        if st.button(f"🤖 AI تحليل ({min(len(df),20)})", key=f"ai_bulk_{section}"):
            with st.spinner("🤖 جاري التحليل..."):
                from utils.ai_helper import bulk_analyze
                result = bulk_analyze(df.head(20).to_dict("records"), section)
                st.markdown(result)


def show_results_page(title, decision_key, section_id, make_type="update"):
    """الدالة الرئيسية — تُستدعى من كل صفحة نتائج"""
    st.title(title)

    if "results" not in st.session_state or st.session_state.results is None:
        st.warning("⚠️ لا توجد نتائج — انتقل لصفحة التحليل وارفع الملفات")
        return

    df = st.session_state.results
    if "القرار" not in df.columns:
        st.error("❌ بيانات التحليل غير مكتملة"); return

    if decision_key == "مفقود":
        missing = st.session_state.get("missing")
        if missing is None or len(missing) == 0:
            st.info("✅ لا توجد منتجات مفقودة — ممتاز!"); return
        filtered = _apply_filters(missing, section_id)
        if len(filtered) == 0:
            st.info("لا توجد نتائج بهذه الفلاتر"); return
        _display_table(filtered, section_id)
        _export_make_bar(filtered, section_id, make_type="new")
    else:
        section_df = df[df["القرار"].str.contains(decision_key, na=False)].copy()
        if len(section_df) == 0:
            st.success(f"✅ لا توجد منتجات في هذا القسم"); return
        # ملخص سريع
        c1, c2, c3 = st.columns(3)
        if "الفرق" in section_df.columns:
            c1.metric("متوسط الفرق", f"{section_df['الفرق'].mean():+.1f} ر.س")
            c2.metric("أكبر فرق", f"{section_df['الفرق'].abs().max():.0f} ر.س")
        c3.metric("عدد المنتجات", len(section_df))
        st.divider()
        filtered = _apply_filters(section_df, section_id)
        if len(filtered) == 0:
            st.info("لا توجد نتائج بهذه الفلاتر"); return
        _display_table(filtered, section_id)
        _export_make_bar(filtered, section_id, make_type)
