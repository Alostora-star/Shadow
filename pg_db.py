# pg_db.py — قاعدة بيانات PostgreSQL (Supabase)
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import psycopg2
import psycopg2.extras

# ===== CONNECTION =====
def get_conn():
    url = os.environ.get("DATABASE_URL", "")
    conn = psycopg2.connect(url)
    conn.autocommit = False
    return conn

def get_db():
    """Returns connection with RealDictCursor"""
    url = os.environ.get("DATABASE_URL", "")
    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

# ===== INIT TABLES =====
def init_web_tables():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS web_users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            avatar_url TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS web_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER REFERENCES web_users(id) ON DELETE CASCADE,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Web tables initialized")

# ===== HELPERS =====
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def make_token() -> str:
    return secrets.token_hex(32)

# ===== AUTH =====
def register_user(name, email, phone, password):
    conn = get_db()
    cur = conn.cursor()
    try:
        # Check duplicate email
        cur.execute("SELECT id FROM web_users WHERE email=%s", (email.lower(),))
        if cur.fetchone():
            return None, "البريد الإلكتروني مستخدم بالفعل"
        # Check duplicate phone
        if phone:
            cur.execute("SELECT id FROM web_users WHERE phone=%s", (phone,))
            if cur.fetchone():
                return None, "رقم الهاتف مستخدم بالفعل"
        ph = hash_pw(password)
        cur.execute(
            "INSERT INTO web_users (name, email, phone, password_hash) VALUES (%s,%s,%s,%s) RETURNING id",
            (name, email.lower(), phone or None, ph)
        )
        uid = cur.fetchone()["id"]
        # Create session
        token = make_token()
        expires = datetime.utcnow() + timedelta(days=30)
        cur.execute(
            "INSERT INTO web_sessions (token, user_id, expires_at) VALUES (%s,%s,%s)",
            (token, uid, expires)
        )
        conn.commit()
        user = get_user_by_id(uid)
        return token, user
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        cur.close(); conn.close()

def login_user(identifier, password):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM web_users WHERE email=%s OR phone=%s",
            (identifier.lower(), identifier)
        )
        row = cur.fetchone()
        if not row:
            return None, "الحساب غير موجود"
        if row["password_hash"] != hash_pw(password):
            return None, "كلمة المرور غير صحيحة"
        token = make_token()
        expires = datetime.utcnow() + timedelta(days=30)
        cur.execute(
            "INSERT INTO web_sessions (token, user_id, expires_at) VALUES (%s,%s,%s) ON CONFLICT (token) DO NOTHING",
            (token, row["id"], expires)
        )
        conn.commit()
        return token, dict(row)
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        cur.close(); conn.close()

def verify_token(token):
    """Returns user_id if valid"""
    if not token:
        return None
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT user_id FROM web_sessions WHERE token=%s AND expires_at > NOW()",
            (token,)
        )
        row = cur.fetchone()
        return row["user_id"] if row else None
    finally:
        cur.close(); conn.close()

def logout_user(token):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM web_sessions WHERE token=%s", (token,))
    conn.commit()
    cur.close(); conn.close()

# ===== USER =====
def get_user_by_id(uid):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM web_users WHERE id=%s", (uid,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        cur.close(); conn.close()

def update_user(uid, **fields):
    if not fields:
        return None, "لا توجد بيانات للتحديث"
    conn = get_db()
    cur = conn.cursor()
    try:
        # Check duplicates for email/phone
        if "email" in fields:
            cur.execute("SELECT id FROM web_users WHERE email=%s AND id!=%s", (fields["email"].lower(), uid))
            if cur.fetchone():
                return None, "البريد الإلكتروني مستخدم بالفعل"
            fields["email"] = fields["email"].lower()
        if "phone" in fields and fields["phone"]:
            cur.execute("SELECT id FROM web_users WHERE phone=%s AND id!=%s", (fields["phone"], uid))
            if cur.fetchone():
                return None, "رقم الهاتف مستخدم بالفعل"
        if "password" in fields:
            fields["password_hash"] = hash_pw(fields.pop("password"))
        
        set_clause = ", ".join(f"{k}=%s" for k in fields)
        vals = list(fields.values()) + [uid]
        cur.execute(f"UPDATE web_users SET {set_clause} WHERE id=%s RETURNING *", vals)
        row = cur.fetchone()
        conn.commit()
        return dict(row) if row else None, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        cur.close(); conn.close()

# ===== BOT DATA (read from bot's SQLite via same Supabase) =====
def get_bot_balance(telegram_id):
    """جلب رصيد المستخدم من جدول البوت على Supabase"""
    if not telegram_id:
        return 0.0
    conn = get_db()
    cur = conn.cursor()
    try:
        # Bot stores users in 'users' table with user_id = telegram_id
        cur.execute("SELECT balance FROM users WHERE user_id=%s", (telegram_id,))
        row = cur.fetchone()
        return float(row["balance"]) if row else 0.0
    except:
        return 0.0
    finally:
        cur.close(); conn.close()

def get_bot_orders(telegram_id):
    """جلب طلبات المستخدم من جدول البوت"""
    if not telegram_id:
        return []
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM purchases_history WHERE user_id=%s ORDER BY timestamp DESC LIMIT 50",
            (telegram_id,)
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    except:
        return []
    finally:
        cur.close(); conn.close()

def get_exchange_rate():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT value FROM settings WHERE key='usd_to_syp'")
        row = cur.fetchone()
        return float(row["value"]) if row else 13000.0
    except:
        return 13000.0
    finally:
        cur.close(); conn.close()

def link_telegram(uid, telegram_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        # Check if tg_id already linked to another
        cur.execute("SELECT id FROM web_users WHERE telegram_id=%s AND id!=%s", (telegram_id, uid))
        if cur.fetchone():
            return False, "هذا الحساب مربوط بحساب آخر"
        cur.execute("UPDATE web_users SET telegram_id=%s WHERE id=%s", (telegram_id, uid))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close(); conn.close()
