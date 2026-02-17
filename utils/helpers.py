"""
utils/helpers.py - دوال مساعدة
"""
import pandas as pd
import io


def safe_float(value):
    """تحويل آمن لـ float"""
    try:
        return float(str(value).replace(",", ""))
    except:
        return 0.0


def format_price(price):
    """تنسيق السعر"""
    return f"{price:,.0f} ر.س"


def format_diff(diff):
    """تنسيق الفرق"""
    if diff > 0:
        return f"+{diff:,.0f} ر.س"
    else:
        return f"{diff:,.0f} ر.س"


def apply_filters(df, filters):
    """تطبيق الفلاتر على DataFrame"""
    filtered = df.copy()
    
    # بحث نصي
    if filters.get("search"):
        search = filters["search"].lower()
        filtered = filtered[
            filtered.apply(lambda r: search in str(r.values).lower(), axis=1)
        ]
    
    # فلتر الماركة
    if filters.get("brand") and filters["brand"] != "الكل":
        if "الماركة" in filtered.columns:
            filtered = filtered[
                filtered["الماركة"].str.contains(filters["brand"], case=False, na=False)
            ]
    
    # فلتر المنافس
    if filters.get("competitor") and filters["competitor"] != "الكل":
        if "المنافس" in filtered.columns:
            filtered = filtered[
                filtered["المنافس"].str.contains(filters["competitor"], case=False, na=False)
            ]
    
    # فلتر النوع
    if filters.get("type") and filters["type"] != "الكل":
        if "النوع" in filtered.columns:
            filtered = filtered[
                filtered["النوع"].str.contains(filters["type"], case=False, na=False)
            ]
    
    # فلتر نسبة التطابق
    if filters.get("match_min"):
        if "نسبة التطابق" in filtered.columns:
            filtered = filtered[filtered["نسبة التطابق"] >= filters["match_min"]]
    
    # فلتر السعر
    if filters.get("price_min") and filters["price_min"] > 0:
        if "السعر" in filtered.columns:
            filtered = filtered[filtered["السعر"] >= filters["price_min"]]
    
    if filters.get("price_max") and filters["price_max"] > 0:
        if "السعر" in filtered.columns:
            filtered = filtered[filtered["السعر"] <= filters["price_max"]]
    
    return filtered


def get_filter_options(df):
    """استخراج خيارات الفلاتر من DataFrame"""
    brands = ["الكل"]
    competitors = ["الكل"]
    types = ["الكل"]
    
    if "الماركة" in df.columns:
        brands += sorted(df["الماركة"].dropna().unique().tolist())
    
    if "المنافس" in df.columns:
        competitors += sorted(df["المنافس"].dropna().unique().tolist())
    
    if "النوع" in df.columns:
        types += sorted(df["النوع"].dropna().unique().tolist())
    
    return {
        "brands": brands,
        "competitors": competitors,
        "types": types
    }


def export_to_excel(df, sheet_name="النتائج"):
    """تصدير DataFrame لـ Excel"""
    output = io.BytesIO()
    
    # نسخ وحذف الأعمدة الثقيلة
    edf = df.copy()
    for col in ["جميع المنافسين", "جميع_المنافسين"]:
        if col in edf.columns:
            edf = edf.drop(columns=[col])
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        edf.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    
    return output.getvalue()


def export_multiple_sheets(dataframes_dict):
    """تصدير عدة DataFrames لـ Excel"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dataframes_dict.items():
            if df is not None and not df.empty:
                edf = df.copy()
                for col in ["جميع المنافسين", "جميع_المنافسين"]:
                    if col in edf.columns:
                        edf = edf.drop(columns=[col])
                edf.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    
    return output.getvalue()


def parse_pasted_text(text):
    """تحويل نص ملصوق لـ DataFrame"""
    try:
        return pd.read_csv(io.StringIO(text), sep=None, engine='python')
    except:
        return pd.DataFrame()
