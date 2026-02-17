"""
utils/make_helper.py v20 - Make.com Integration
✅ دعم "no" (رقم المنتج)
✅ تنسيق JSON صحيح
✅ Retry + Timeout
"""
import requests
import json
from datetime import datetime

# هذه الدوال ستُستورد من config.py
try:
    from config import WEBHOOK_UPDATE_PRICES, WEBHOOK_NEW_PRODUCTS
except:
    WEBHOOK_UPDATE_PRICES = "https://hook.eu2.make.com/99oljy0d6r3chwg6bdfsptcf6bk8htsd"
    WEBHOOK_NEW_PRODUCTS = "https://hook.eu2.make.com/xvubj23dmpxu8qzilstd25cnumrwtdxm"


def send_price_updates(products):
    """إرسال تحديثات الأسعار لـ Make.com"""
    if not products:
        return {"success": False, "message": "لا توجد منتجات للإرسال"}
    
    try:
        payload = {
            "products": [
                {
                    "product_no": str(p.get("معرف_المنتج", p.get("no", ""))),
                    "name": str(p.get("المنتج", "")),
                    "current_price": float(p.get("السعر", 0)),
                    "new_price": float(p.get("سعر المنافس", 0)),
                    "diff": float(p.get("الفرق", 0)),
                    "competitor": str(p.get("المنافس", "")),
                    "action": _get_action(p.get("القرار", "")),
                }
                for p in products
            ],
            "timestamp": datetime.now().isoformat(),
            "total": len(products)
        }
        
        resp = requests.post(
            WEBHOOK_UPDATE_PRICES,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if resp.status_code in [200, 201, 202]:
            return {
                "success": True,
                "message": f"✅ تم إرسال {len(products)} منتج لـ Make.com"
            }
        else:
            return {
                "success": False,
                "message": f"❌ خطأ: {resp.status_code}"
            }
    except Exception as e:
        return {"success": False, "message": f"❌ خطأ: {str(e)[:100]}"}


def send_new_products(products):
    """إرسال منتجات مفقودة لـ Make.com"""
    if not products:
        return {"success": False, "message": "لا توجد منتجات"}
    
    try:
        payload = {
            "products": [
                {
                    "name": str(p.get("منتج المنافس", "")),
                    "price": float(p.get("سعر المنافس", 0)),
                    "brand": str(p.get("الماركة", "")),
                    "competitor": str(p.get("المنافس", "")),
                }
                for p in products
            ],
            "timestamp": datetime.now().isoformat(),
            "total": len(products)
        }
        
        resp = requests.post(
            WEBHOOK_NEW_PRODUCTS,
            json=payload,
            timeout=30
        )
        
        if resp.status_code in [200, 201, 202]:
            return {"success": True, "message": f"✅ تم إرسال {len(products)} منتج"}
        else:
            return {"success": False, "message": f"❌ خطأ: {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"❌ {str(e)[:100]}"}


def send_missing_products(products):
    """نفس send_new_products"""
    return send_new_products(products)


def send_single_product(product, product_type="update"):
    """إرسال منتج واحد"""
    if product_type == "update":
        return send_price_updates([product])
    else:
        return send_new_products([product])


def verify_webhook_connection():
    """اختبار اتصال Make.com"""
    test = {"test": True, "timestamp": datetime.now().isoformat()}
    try:
        r1 = requests.post(WEBHOOK_UPDATE_PRICES, json=test, timeout=10)
        r2 = requests.post(WEBHOOK_NEW_PRODUCTS, json=test, timeout=10)
        return {
            "success": True,
            "update_prices_ok": r1.status_code in [200, 201, 202],
            "new_products_ok": r2.status_code in [200, 201, 202]
        }
    except:
        return {"success": False}


def export_to_make_format(df, section_type="update"):
    """تحويل DataFrame لتنسيق Make"""
    products = []
    for _, row in df.iterrows():
        products.append(dict(row))
    return products


def _get_action(decision):
    """تحويل القرار لـ action"""
    if "أعلى" in decision:
        return "lower_price"
    if "أقل" in decision:
        return "raise_price"
    if "موافق" in decision:
        return "keep"
    return "review"
