"""
utils/make_helper.py — تكامل Make.com
"""
import requests
from datetime import datetime
try:
    from config import WEBHOOK_UPDATE_PRICES, WEBHOOK_NEW_PRODUCTS
except Exception:
    WEBHOOK_UPDATE_PRICES = ""
    WEBHOOK_NEW_PRODUCTS  = ""


def _action(decision):
    if "أعلى" in str(decision):  return "lower_price"
    if "أقل"  in str(decision):  return "raise_price"
    if "موافق" in str(decision): return "keep"
    return "review"


def send_price_updates(products):
    if not products:
        return {"success": False, "message": "لا توجد منتجات"}
    try:
        payload = {
            "products": [{
                "product_no":          str(p.get("معرف_المنتج", p.get("no", ""))),
                "name":                str(p.get("المنتج", "")),
                "current_price":       float(p.get("السعر", 0)),
                "competitor_price":    float(p.get("سعر_المنافس", p.get("سعر المنافس", 0))),
                "diff":                float(p.get("الفرق", 0)),
                "action":              _action(p.get("القرار", "")),
                "competitor":          str(p.get("المنافس", "")),
                "brand":               str(p.get("الماركة", "")),
                "match_score":         float(p.get("نسبة_التطابق", p.get("نسبة التطابق", 0))),
            } for p in products],
            "timestamp": datetime.now().isoformat(),
            "total":     len(products),
            "source":    "mahwous_v20",
        }
        # استبعاد المنتجات بدون رقم
        payload["products"] = [p for p in payload["products"] if p["product_no"]]
        if not payload["products"]:
            return {"success": False, "message": "❌ لا يوجد معرف_المنتج — تأكد من اختيار عمود 'no'"}
        r = requests.post(WEBHOOK_UPDATE_PRICES, json=payload,
                          headers={"Content-Type": "application/json"}, timeout=30)
        if r.status_code in (200, 201, 202):
            return {"success": True,
                    "message": f"✅ تم إرسال {len(payload['products'])} منتج لـ Make.com",
                    "count": len(payload["products"])}
        return {"success": False, "message": f"❌ Make رد بـ {r.status_code}"}
    except requests.Timeout:
        return {"success": False, "message": "❌ انتهت مهلة الاتصال"}
    except Exception as e:
        return {"success": False, "message": f"❌ خطأ: {str(e)[:120]}"}


def send_new_products(products):
    if not products:
        return {"success": False, "message": "لا توجد منتجات"}
    try:
        payload = {
            "products": [{
                "name":       str(p.get("منتج المنافس", "")),
                "price":      float(p.get("سعر المنافس", 0)),
                "brand":      str(p.get("الماركة", "")),
                "size":       str(p.get("الحجم", "")),
                "type":       str(p.get("النوع", "")),
                "competitor": str(p.get("المنافس", "")),
            } for p in products],
            "timestamp": datetime.now().isoformat(),
            "total":     len(products),
            "source":    "mahwous_v20",
        }
        r = requests.post(WEBHOOK_NEW_PRODUCTS, json=payload,
                          headers={"Content-Type": "application/json"}, timeout=30)
        if r.status_code in (200, 201, 202):
            return {"success": True,
                    "message": f"✅ تم إرسال {len(products)} منتج مفقود لـ Make.com",
                    "count": len(products)}
        return {"success": False, "message": f"❌ Make رد بـ {r.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"❌ خطأ: {str(e)[:120]}"}


def test_connection():
    test = {"test": True, "timestamp": datetime.now().isoformat(),
            "source": "mahwous_v20"}
    results = {}
    for name, url in [("تحديث الأسعار", WEBHOOK_UPDATE_PRICES),
                      ("منتجات جديدة",  WEBHOOK_NEW_PRODUCTS)]:
        try:
            r = requests.post(url, json=test, timeout=10)
            results[name] = r.status_code in (200, 201, 202)
        except Exception:
            results[name] = False
    ok = all(results.values())
    return {"success": ok, "details": results}
