"""
utils/make_helper.py v20.0 - Make.com Integration محسّن
✅ دعم رقم المنتج "no"
✅ تنسيق JSON صحيح 100%
✅ retry + timeout
"""
import requests, json
from datetime import datetime
from config import WEBHOOK_UPDATE_PRICES, WEBHOOK_NEW_PRODUCTS

def _get_action(decision):
    """تحويل القرار العربي لـ action إنجليزي"""
    if "أعلى" in decision: return "lower_price"
    if "أقل" in decision: return "raise_price"
    if "موافق" in decision: return "keep"
    return "review"

def _get_priority(product):
    """تحديد أولوية إضافة المنتج المفقود"""
    price = float(product.get("سعر المنافس", 0))
    brand = str(product.get("الماركة", "")).lower()
    # علامات فاخرة = أولوية عالية
    premium = ["dior","chanel","tom ford","creed","amouage"]
    if any(b in brand for b in premium):
        return "high"
    if price > 300:
        return "high"
    if price > 150:
        return "medium"
    return "low"

def send_price_updates(products):
    """
    إرسال تحديثات الأسعار لـ Make.com
    
    Format:
    {
        "products": [{
            "product_no": "12345",        ← مهم جداً!
            "name": "...",
            "current_price": 450.00,
            "new_price": 430.00,
            "diff": -20.00,
            "competitor": "competitor1",
            "action": "lower_price",
            "reason": "..."
        }],
        "timestamp": "2026-02-17T...",
        "total": 10
    }
    """
    if not products:
        return {"success": False, "message": "لا توجد منتجات للإرسال"}

    try:
        payload = {
            "products": [{
                "product_no": str(p.get("معرف_المنتج", p.get("معرف المنتج", p.get("no", p.get("NO", ""))))),
                "name": str(p.get("المنتج", "")),
                "current_price": float(p.get("السعر", 0)),
                "new_price": float(p.get("سعر_مقترح", p.get("سعر المنافس", 0))),
                "diff": float(p.get("الفرق", 0)),
                "competitor": str(p.get("المنافس", "")),
                "competitor_product": str(p.get("منتج المنافس", "")),
                "action": _get_action(p.get("القرار", "")),
                "reason": str(p.get("التفسير", ""))[:200],
                "brand": str(p.get("الماركة", "")),
                "size": str(p.get("الحجم", "")),
                "match_confidence": float(p.get("نسبة التطابق", 0)),
            } for p in products if p.get("معرف_المنتج") or p.get("no")],
            "timestamp": datetime.now().isoformat(),
            "total": len(products),
            "source": "mahwous_v20"
        }

        if not payload["products"]:
            return {"success": False, "message": "❌ لا يوجد رقم منتج 'no' في أي منتج"}

        resp = requests.post(
            WEBHOOK_UPDATE_PRICES,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if resp.status_code in [200, 201, 202]:
            return {
                "success": True,
                "message": f"✅ تم إرسال {len(payload['products'])} منتج لـ Make.com",
                "sent_count": len(payload["products"])
            }
        else:
            return {
                "success": False,
                "message": f"❌ خطأ من Make: {resp.status_code} - {resp.text[:100]}"
            }

    except requests.exceptions.Timeout:
        return {"success": False, "message": "❌ انتهت مهلة الاتصال بـ Make"}
    except Exception as e:
        return {"success": False, "message": f"❌ خطأ: {str(e)[:100]}"}


def send_new_products(products):
    """
    إرسال منتجات مفقودة لـ Make.com
    
    Format:
    {
        "products": [{
            "name": "...",
            "price": 450.00,
            "brand": "Dior",
            "size": "100ml",
            "type": "EDP",
            "competitor": "competitor1",
            "priority": "high",
            "image_url": "https://...",
            "description": "وصف مهووس..."
        }],
        "timestamp": "...",
        "total": 15
    }
    """
    if not products:
        return {"success": False, "message": "لا توجد منتجات للإرسال"}

    try:
        payload = {
            "products": [{
                "name": str(p.get("منتج المنافس", "")),
                "price": float(p.get("سعر المنافس", 0)),
                "brand": str(p.get("الماركة", "")),
                "size": str(p.get("الحجم", "")),
                "type": str(p.get("النوع", "")),
                "gender": str(p.get("الجنس", "")),
                "competitor": str(p.get("المنافس", "")),
                "competitor_product_id": str(p.get("معرف المنافس", "")),
                "priority": _get_priority(p),
                "image_url": str(p.get("image_url", "")),
                "description": str(p.get("وصف_مهووس", ""))[:500],
                "top_notes": p.get("top_notes", []),
                "middle_notes": p.get("middle_notes", []),
                "base_notes": p.get("base_notes", []),
            } for p in products],
            "timestamp": datetime.now().isoformat(),
            "total": len(products),
            "source": "mahwous_v20"
        }

        resp = requests.post(
            WEBHOOK_NEW_PRODUCTS,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if resp.status_code in [200, 201, 202]:
            return {
                "success": True,
                "message": f"✅ تم إرسال {len(payload['products'])} منتج مفقود لـ Make.com",
                "sent_count": len(payload["products"])
            }
        else:
            return {
                "success": False,
                "message": f"❌ خطأ من Make: {resp.status_code}"
            }

    except Exception as e:
        return {"success": False, "message": f"❌ خطأ: {str(e)[:100]}"}


def send_single_product(product, product_type="update"):
    """إرسال منتج واحد"""
    if product_type == "update":
        return send_price_updates([product])
    else:
        return send_new_products([product])


def verify_webhook_connection():
    """اختبار اتصال Make.com"""
    test = {
        "test": True,
        "timestamp": datetime.now().isoformat(),
        "message": "اختبار اتصال من مهووس v20"
    }
    try:
        r1 = requests.post(WEBHOOK_UPDATE_PRICES, json=test, timeout=10)
        r2 = requests.post(WEBHOOK_NEW_PRODUCTS, json=test, timeout=10)
        return {
            "success": True,
            "update_prices_ok": r1.status_code in [200,201,202],
            "new_products_ok": r2.status_code in [200,201,202]
        }
    except:
        return {"success": False}


def export_to_make_format(df, section_type="update"):
    """تحويل DataFrame لتنسيق Make"""
    products = []
    for _, row in df.iterrows():
        products.append({
            "معرف_المنتج": row.get("معرف_المنتج", row.get("معرف المنتج", row.get("no", ""))),
            "المنتج": row.get("المنتج", ""),
            "السعر": row.get("السعر", 0),
            "سعر المنافس": row.get("سعر المنافس", row.get("سعر_المنافس", 0)),
            "الفرق": row.get("الفرق", 0),
            "القرار": row.get("القرار", ""),
            "المنافس": row.get("المنافس", ""),
            "التفسير": row.get("التفسير", ""),
            "الماركة": row.get("الماركة", ""),
            "الحجم": row.get("الحجم", ""),
            "نسبة التطابق": row.get("نسبة التطابق", row.get("نسبة_التطابق", 0)),
        })
    return products
