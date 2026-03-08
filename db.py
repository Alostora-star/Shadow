# db.py — قاعدة بيانات الموقع (Supabase)
import os, hashlib, secrets
from datetime import datetime, timedelta
import psycopg2, psycopg2.extras

URL = os.environ["DATABASE_URL"]

def conn():
    c = psycopg2.connect(URL, cursor_factory=psycopg2.extras.RealDictCursor)
    c.autocommit = False
    return c

def init_tables():
    c = conn(); cur = c.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS ss_users (
        id SERIAL PRIMARY KEY, name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL, phone TEXT UNIQUE,
        password_hash TEXT NOT NULL, balance REAL DEFAULT 0.0,
        is_admin BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW())""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ss_sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER REFERENCES ss_users(id) ON DELETE CASCADE,
        expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW())""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ss_deposits (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES ss_users(id) ON DELETE CASCADE,
        amount REAL NOT NULL, method TEXT NOT NULL,
        tx_number TEXT NOT NULL, screenshot_url TEXT,
        status TEXT DEFAULT 'pending', admin_note TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(), reviewed_at TIMESTAMPTZ)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ss_orders (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES ss_users(id) ON DELETE CASCADE,
        game_id TEXT NOT NULL, game_name TEXT NOT NULL,
        product_id TEXT NOT NULL, product_name TEXT NOT NULL,
        player_id TEXT NOT NULL, price REAL NOT NULL,
        status TEXT DEFAULT 'pending', admin_note TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(), completed_at TIMESTAMPTZ)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ss_settings (
        key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
    for k,v in [('usd_to_syp','13000'),('shamcash_number','09XXXXXXXX'),
                ('syriatel_number','09XXXXXXXX'),('admin_tg_id','7524378240'),
                ('bot_token','')]:
        cur.execute("INSERT INTO ss_settings(key,value) VALUES(%s,%s) ON CONFLICT DO NOTHING",(k,v))
    c.commit(); cur.close(); c.close()
    print("✅ Tables ready")

def hp(pw): return hashlib.sha256(pw.encode()).hexdigest()
def tok():  return secrets.token_hex(32)

# AUTH
def register_user(name, email, phone, password):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT id FROM ss_users WHERE email=%s",(email.lower(),))
        if cur.fetchone(): return None,"البريد الإلكتروني مستخدم بالفعل"
        if phone:
            cur.execute("SELECT id FROM ss_users WHERE phone=%s",(phone,))
            if cur.fetchone(): return None,"رقم الهاتف مستخدم بالفعل"
        cur.execute("INSERT INTO ss_users(name,email,phone,password_hash) VALUES(%s,%s,%s,%s) RETURNING *",
                    (name,email.lower(),phone or None,hp(password)))
        user = dict(cur.fetchone())
        token = tok()
        cur.execute("INSERT INTO ss_sessions(token,user_id,expires_at) VALUES(%s,%s,%s)",
                    (token,user["id"],datetime.utcnow()+timedelta(days=30)))
        c.commit(); return token, user
    except Exception as e:
        c.rollback(); return None, str(e)
    finally: cur.close(); c.close()

def login_user(identifier, password):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT * FROM ss_users WHERE email=%s OR phone=%s",
                    (identifier.lower(),identifier))
        row = cur.fetchone()
        if not row: return None,"الحساب غير موجود"
        if row["password_hash"] != hp(password): return None,"كلمة المرور غير صحيحة"
        token = tok()
        cur.execute("INSERT INTO ss_sessions(token,user_id,expires_at) VALUES(%s,%s,%s)",
                    (token,row["id"],datetime.utcnow()+timedelta(days=30)))
        c.commit(); return token, dict(row)
    except Exception as e:
        c.rollback(); return None, str(e)
    finally: cur.close(); c.close()

def verify_token(token):
    if not token: return None
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT user_id FROM ss_sessions WHERE token=%s AND expires_at>NOW()",(token,))
        row = cur.fetchone()
        return row["user_id"] if row else None
    finally: cur.close(); c.close()

def logout_user(token):
    c = conn(); cur = c.cursor()
    cur.execute("DELETE FROM ss_sessions WHERE token=%s",(token,))
    c.commit(); cur.close(); c.close()

# USERS
def get_user(uid):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT * FROM ss_users WHERE id=%s",(uid,))
        row = cur.fetchone(); return dict(row) if row else None
    finally: cur.close(); c.close()

def update_user(uid, **fields):
    if not fields: return None,"لا توجد بيانات"
    c = conn(); cur = c.cursor()
    try:
        if "email" in fields:
            cur.execute("SELECT id FROM ss_users WHERE email=%s AND id!=%s",(fields["email"].lower(),uid))
            if cur.fetchone(): return None,"البريد مستخدم بالفعل"
            fields["email"] = fields["email"].lower()
        if "phone" in fields and fields["phone"]:
            cur.execute("SELECT id FROM ss_users WHERE phone=%s AND id!=%s",(fields["phone"],uid))
            if cur.fetchone(): return None,"رقم الهاتف مستخدم بالفعل"
        if "password" in fields:
            fields["password_hash"] = hp(fields.pop("password"))
        sets = ", ".join(f"{k}=%s" for k in fields)
        cur.execute(f"UPDATE ss_users SET {sets} WHERE id=%s RETURNING *",list(fields.values())+[uid])
        row = cur.fetchone(); c.commit()
        return dict(row) if row else None, None
    except Exception as e:
        c.rollback(); return None, str(e)
    finally: cur.close(); c.close()

# DEPOSITS
def create_deposit(user_id, amount, method, tx_number, screenshot_url=None):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("""INSERT INTO ss_deposits(user_id,amount,method,tx_number,screenshot_url)
                       VALUES(%s,%s,%s,%s,%s) RETURNING *""",
                    (user_id,amount,method,tx_number,screenshot_url))
        row = dict(cur.fetchone()); c.commit(); return row
    except Exception as e:
        c.rollback(); return None
    finally: cur.close(); c.close()

def approve_deposit(deposit_id, admin_note=""):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT * FROM ss_deposits WHERE id=%s AND status='pending'",(deposit_id,))
        dep = cur.fetchone()
        if not dep: return False,"الطلب غير موجود أو تمت معالجته"
        cur.execute("UPDATE ss_deposits SET status='approved',admin_note=%s,reviewed_at=NOW() WHERE id=%s",
                    (admin_note,deposit_id))
        cur.execute("UPDATE ss_users SET balance=balance+%s WHERE id=%s",(dep["amount"],dep["user_id"]))
        c.commit(); return True, dict(dep)
    except Exception as e:
        c.rollback(); return False, str(e)
    finally: cur.close(); c.close()

def reject_deposit(deposit_id, reason=""):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("UPDATE ss_deposits SET status='rejected',admin_note=%s,reviewed_at=NOW() WHERE id=%s AND status='pending'",
                    (reason,deposit_id))
        c.commit(); return cur.rowcount > 0
    except Exception as e:
        c.rollback(); return False
    finally: cur.close(); c.close()

def get_pending_deposits():
    c = conn(); cur = c.cursor()
    try:
        cur.execute("""SELECT d.*,u.name,u.email FROM ss_deposits d
                       JOIN ss_users u ON d.user_id=u.id
                       WHERE d.status='pending' ORDER BY d.created_at DESC""")
        return [dict(r) for r in cur.fetchall()]
    finally: cur.close(); c.close()

def get_user_deposits(uid):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT * FROM ss_deposits WHERE user_id=%s ORDER BY created_at DESC LIMIT 20",(uid,))
        return [dict(r) for r in cur.fetchall()]
    finally: cur.close(); c.close()

# ORDERS
def create_order(user_id, game_id, game_name, product_id, product_name, player_id, price):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT balance FROM ss_users WHERE id=%s FOR UPDATE",(user_id,))
        row = cur.fetchone()
        if not row or row["balance"] < price: return None,"رصيدك غير كافٍ"
        cur.execute("UPDATE ss_users SET balance=balance-%s WHERE id=%s",(price,user_id))
        cur.execute("""INSERT INTO ss_orders(user_id,game_id,game_name,product_id,product_name,player_id,price)
                       VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                    (user_id,game_id,game_name,product_id,product_name,player_id,price))
        order = dict(cur.fetchone()); c.commit(); return order, None
    except Exception as e:
        c.rollback(); return None, str(e)
    finally: cur.close(); c.close()

def complete_order(order_id, admin_note=""):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("""UPDATE ss_orders SET status='completed',admin_note=%s,completed_at=NOW()
                       WHERE id=%s AND status='pending' RETURNING *""",(admin_note,order_id))
        row = cur.fetchone(); c.commit()
        return dict(row) if row else None
    except Exception as e:
        c.rollback(); return None
    finally: cur.close(); c.close()

def refund_order(order_id, reason=""):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT * FROM ss_orders WHERE id=%s AND status='pending'",(order_id,))
        ord_ = cur.fetchone()
        if not ord_: return False
        cur.execute("UPDATE ss_orders SET status='refunded',admin_note=%s,completed_at=NOW() WHERE id=%s",
                    (reason,order_id))
        cur.execute("UPDATE ss_users SET balance=balance+%s WHERE id=%s",(ord_["price"],ord_["user_id"]))
        c.commit(); return True
    except Exception as e:
        c.rollback(); return False
    finally: cur.close(); c.close()

def get_pending_orders():
    c = conn(); cur = c.cursor()
    try:
        cur.execute("""SELECT o.*,u.name,u.email FROM ss_orders o
                       JOIN ss_users u ON o.user_id=u.id
                       WHERE o.status='pending' ORDER BY o.created_at DESC""")
        return [dict(r) for r in cur.fetchall()]
    finally: cur.close(); c.close()

def get_user_orders(uid):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT * FROM ss_orders WHERE user_id=%s ORDER BY created_at DESC LIMIT 30",(uid,))
        return [dict(r) for r in cur.fetchall()]
    finally: cur.close(); c.close()

def get_setting(key, default=""):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT value FROM ss_settings WHERE key=%s",(key,))
        row = cur.fetchone(); return row["value"] if row else default
    finally: cur.close(); c.close()

def set_setting(key, value):
    c = conn(); cur = c.cursor()
    cur.execute("INSERT INTO ss_settings(key,value) VALUES(%s,%s) ON CONFLICT(key) DO UPDATE SET value=%s",
                (key,value,value))
    c.commit(); cur.close(); c.close()

def get_all_users():
    c = conn(); cur = c.cursor()
    try:
        cur.execute("SELECT id,name,email,phone,balance,is_admin,created_at FROM ss_users ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]
    finally: cur.close(); c.close()

def admin_set_balance(uid, amount):
    c = conn(); cur = c.cursor()
    cur.execute("UPDATE ss_users SET balance=%s WHERE id=%s",(amount,uid))
    c.commit(); cur.close(); c.close()
