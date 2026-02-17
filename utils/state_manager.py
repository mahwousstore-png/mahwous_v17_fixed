"""
utils/state_manager.py - إدارة الذاكرة والحفظ التلقائي
"""
import pickle, gzip, os
from datetime import datetime

STATE_FILE = "mahwous_state.pkl.gz"

def save_state(data):
    """حفظ حالة التطبيق (النتائج، الإعدادات)"""
    try:
        state = {
            "results": data.get("results"),
            "missing": data.get("missing"),
            "our_file": data.get("our_file"),
            "comp_files": data.get("comp_files"),
            "timestamp": datetime.now().isoformat(),
            "version": "v20"
        }
        with gzip.open(STATE_FILE, 'wb') as f:
            pickle.dump(state, f)
        return True
    except Exception as e:
        print(f"Save error: {e}")
        return False

def load_state():
    """تحميل آخر حالة محفوظة"""
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with gzip.open(STATE_FILE, 'rb') as f:
            state = pickle.load(f)
        # تحقق من الإصدار
        if state.get("version") == "v20":
            return state
    except:
        pass
    return None

def clear_state():
    """مسح الحالة المحفوظة"""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
