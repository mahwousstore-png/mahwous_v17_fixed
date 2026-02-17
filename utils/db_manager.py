"""
utils/db_manager.py - إدارة قاعدة البيانات (مبسّط)
"""
import sqlite3
from datetime import datetime


DB_PATH = "perfume_pricing.db"


def init_db():
    """إنشاء قاعدة البيانات"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # جدول الأحداث
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page TEXT,
                action TEXT,
                details TEXT,
                timestamp TEXT
            )
        """)
        
        # جدول القرارات
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT,
                section TEXT,
                decision TEXT,
                reason TEXT,
                our_price REAL,
                comp_price REAL,
                price_diff REAL,
                competitor TEXT,
                timestamp TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    except:
        pass


def log_event(page, action, details=""):
    """تسجيل حدث"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO events (page, action, details, timestamp) VALUES (?, ?, ?, ?)",
            (page, action, details, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except:
        pass


def log_decision(product_name, section, decision, reason="", 
                 our_price=0, comp_price=0, price_diff=0, competitor=""):
    """تسجيل قرار"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """INSERT INTO decisions 
               (product_name, section, decision, reason, our_price, comp_price, 
                price_diff, competitor, timestamp) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_name, section, decision, reason, our_price, comp_price,
             price_diff, competitor, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except:
        pass


def get_events(limit=50):
    """استرجاع الأحداث"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        )
        events = cursor.fetchall()
        conn.close()
        return events
    except:
        return []


def get_decisions(limit=50):
    """استرجاع القرارات"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)
        )
        decisions = cursor.fetchall()
        conn.close()
        return decisions
    except:
        return []


# دوال أخرى - stubs لتجنب ImportError
def log_analysis(*args, **kwargs):
    pass

def get_analysis_history(*args, **kwargs):
    return []

def upsert_price_history(*args, **kwargs):
    pass

def get_price_history(*args, **kwargs):
    return []

def get_price_changes(*args, **kwargs):
    return []

def save_job_progress(*args, **kwargs):
    pass

def get_job_progress(*args, **kwargs):
    return None

def get_last_job(*args, **kwargs):
    return None
