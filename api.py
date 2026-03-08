# api.py — Shadow Store REST API
# يعمل بجانب البوت على نفس السيرفر

import sqlite3
import os
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import DATABASE_NAME, BOT_TOKEN, ADMIN_USER_ID

app = Flask(__name__)
CORS(app, origins="*")  # السماح لأي موقع بالوصول

# ===== SESSIONS TABLE =====
def init_sessions():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS web_sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS web_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        email TEXT UNIQUE,
        phone TEXT,
        name TEXT NOT NULL,
        password_hash TEXT,
        avatar_url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def make_token() -> str:
    return secrets.token_hex(32)

def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def verify_token(token: str):
    """Returns user_id if token valid, else None"""
    if not token:
        return None
    conn = get_db()
    row = conn.execute(
        "SELECT user_id, expires_at FROM web_sessions WHERE token=?", (token,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
        return None
    return row["user_id"]

def get_web_user(uid: int):
    conn = get_db()
    u = conn.execute("SELECT * FROM web_users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return dict(u) if u else None

def get_bot_wallet(telegram_id: int) -> float:
    """جلب رصيد المستخدم من جدول البوت"""
    try:
        conn = get_db()
        row = conn.execute("SELECT balance FROM users WHERE user_id=?", (telegram_id,)).fetchone()
        conn.close()
        return float(row["balance"]) if row else 0.0
    except:
        return 0.0

def get_bot_orders(telegram_id: int) -> list:
    """جلب طلبات المستخدم من جدول البوت"""
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM purchases_history WHERE user_id=? ORDER BY timestamp DESC LIMIT 50",
            (telegram_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except:
        return []

# ===== AUTH ENDPOINTS =====

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name  = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    pw    = data.get("password") or ""

    if not name:  return jsonify({"ok": False, "error": "الاسم مطلوب"}), 400
    if not email: return jsonify({"ok": False, "error": "البريد الإلكتروني مطلوب"}), 400
    if len(pw) < 6: return jsonify({"ok": False, "error": "كلمة المرور يجب أن تكون 6 أحرف على الأقل"}), 400

    conn = get_db()
    # Check duplicates
    if conn.execute("SELECT id FROM web_users WHERE email=?", (email,)).fetchone():
        conn.close()
        return jsonify({"ok": False, "error": "البريد الإلكتروني مستخدم بالفعل"}), 409
    if phone and conn.execute("SELECT id FROM web_users WHERE phone=?", (phone,)).fetchone():
        conn.close()
        return jsonify({"ok": False, "error": "رقم الهاتف مستخدم بالفعل"}), 409

    ph = hash_pw(pw)
    cur = conn.execute(
        "INSERT INTO web_users (name, email, phone, password_hash) VALUES (?,?,?,?)",
        (name, email, phone, ph)
    )
    uid = cur.lastrowid
    conn.commit()
    conn.close()

    token = make_token()
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    conn = get_db()
    conn.execute("INSERT INTO web_sessions (token, user_id, expires_at) VALUES (?,?,?)", (token, uid, expires))
    conn.commit()
    conn.close()

    user = get_web_user(uid)
    return jsonify({"ok": True, "token": token, "user": _safe_user(user, 0.0, [])})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data  = request.get_json() or {}
    ident = (data.get("identifier") or "").strip().lower()
    pw    = data.get("password") or ""

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM web_users WHERE email=? OR phone=?", (ident, ident)
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"ok": False, "error": "الحساب غير موجود"}), 404
    if row["password_hash"] != hash_pw(pw):
        return jsonify({"ok": False, "error": "كلمة المرور غير صحيحة"}), 401

    uid = row["id"]
    token = make_token()
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO web_sessions (token, user_id, expires_at) VALUES (?,?,?)", (token, uid, expires))
    conn.commit()
    conn.close()

    tg_id = row["telegram_id"]
    balance = get_bot_wallet(tg_id) if tg_id else 0.0
    orders  = get_bot_orders(tg_id) if tg_id else []
    return jsonify({"ok": True, "token": token, "user": _safe_user(dict(row), balance, orders)})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    conn = get_db()
    conn.execute("DELETE FROM web_sessions WHERE token=?", (token,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ===== USER ENDPOINTS =====

@app.route("/api/user/me", methods=["GET"])
def me():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    uid = verify_token(token)
    if not uid:
        return jsonify({"ok": False, "error": "غير مصرح"}), 401
    user = get_web_user(uid)
    if not user:
        return jsonify({"ok": False, "error": "المستخدم غير موجود"}), 404
    tg_id = user.get("telegram_id")
    balance = get_bot_wallet(tg_id) if tg_id else 0.0
    orders  = get_bot_orders(tg_id) if tg_id else []
    return jsonify({"ok": True, "user": _safe_user(user, balance, orders)})


@app.route("/api/user/update", methods=["POST"])
def update_user():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    uid = verify_token(token)
    if not uid:
        return jsonify({"ok": False, "error": "غير مصرح"}), 401

    data = request.get_json() or {}
    conn = get_db()
    user = conn.execute("SELECT * FROM web_users WHERE id=?", (uid,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"ok": False, "error": "المستخدم غير موجود"}), 404

    fields = {}
    if "name"  in data and data["name"].strip():  fields["name"]  = data["name"].strip()
    if "email" in data and data["email"].strip():
        ex = conn.execute("SELECT id FROM web_users WHERE email=? AND id!=?", (data["email"].strip().lower(), uid)).fetchone()
        if ex:
            conn.close()
            return jsonify({"ok": False, "error": "البريد مستخدم بالفعل"}), 409
        fields["email"] = data["email"].strip().lower()
    if "phone" in data:
        ph = data["phone"].strip()
        if ph:
            ex = conn.execute("SELECT id FROM web_users WHERE phone=? AND id!=?", (ph, uid)).fetchone()
            if ex:
                conn.close()
                return jsonify({"ok": False, "error": "الرقم مستخدم بالفعل"}), 409
        fields["phone"] = ph
    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            conn.close()
            return jsonify({"ok": False, "error": "كلمة المرور قصيرة جداً"}), 400
        fields["password_hash"] = hash_pw(data["password"])

    if fields:
        set_clause = ", ".join(f"{k}=?" for k in fields)
        vals = list(fields.values()) + [uid]
        conn.execute(f"UPDATE web_users SET {set_clause} WHERE id=?", vals)
        conn.commit()

    updated = conn.execute("SELECT * FROM web_users WHERE id=?", (uid,)).fetchone()
    conn.close()
    tg_id = updated["telegram_id"] if updated else None
    balance = get_bot_wallet(tg_id) if tg_id else 0.0
    orders  = get_bot_orders(tg_id) if tg_id else []
    return jsonify({"ok": True, "user": _safe_user(dict(updated), balance, orders)})


# ===== TELEGRAM LINK =====

@app.route("/api/auth/telegram", methods=["POST"])
def link_telegram():
    """ربط حساب تيليغرام بالحساب الموجود"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    uid = verify_token(token)
    data = request.get_json() or {}
    tg_id = data.get("telegram_id")

    if not tg_id:
        return jsonify({"ok": False, "error": "معرف تيليغرام مطلوب"}), 400

    conn = get_db()
    # Check if tg_id already linked to another account
    ex = conn.execute("SELECT id FROM web_users WHERE telegram_id=? AND id!=?", (tg_id, uid or 0)).fetchone()
    if ex:
        conn.close()
        return jsonify({"ok": False, "error": "هذا الحساب مربوط بحساب آخر"}), 409

    if uid:
        conn.execute("UPDATE web_users SET telegram_id=? WHERE id=?", (tg_id, uid))
    else:
        # Auto login via telegram
        row = conn.execute("SELECT * FROM web_users WHERE telegram_id=?", (tg_id,)).fetchone()
        if not row:
            conn.close()
            return jsonify({"ok": False, "error": "الحساب غير مربوط"}), 404
        uid = row["id"]
        new_token = make_token()
        expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
        conn.execute("INSERT OR REPLACE INTO web_sessions (token, user_id, expires_at) VALUES (?,?,?)", (new_token, uid, expires))
        conn.commit()
        conn.close()
        user = get_web_user(uid)
        balance = get_bot_wallet(tg_id)
        orders  = get_bot_orders(tg_id)
        return jsonify({"ok": True, "token": new_token, "user": _safe_user(user, balance, orders)})

    conn.commit()
    updated = conn.execute("SELECT * FROM web_users WHERE id=?", (uid,)).fetchone()
    conn.close()
    balance = get_bot_wallet(tg_id)
    orders  = get_bot_orders(tg_id)
    return jsonify({"ok": True, "user": _safe_user(dict(updated), balance, orders)})


# ===== ORDERS =====

@app.route("/api/orders", methods=["GET"])
def orders():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    uid = verify_token(token)
    if not uid:
        return jsonify({"ok": False, "error": "غير مصرح"}), 401
    user = get_web_user(uid)
    tg_id = user.get("telegram_id") if user else None
    ords = get_bot_orders(tg_id) if tg_id else []
    return jsonify({"ok": True, "orders": ords})


# ===== WALLET =====

@app.route("/api/wallet", methods=["GET"])
def wallet():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    uid = verify_token(token)
    if not uid:
        return jsonify({"ok": False, "error": "غير مصرح"}), 401
    user = get_web_user(uid)
    tg_id = user.get("telegram_id") if user else None
    balance = get_bot_wallet(tg_id) if tg_id else 0.0
    # Get exchange rate
    try:
        conn = get_db()
        row = conn.execute("SELECT value FROM settings WHERE key='usd_to_syp'").fetchone()
        conn.close()
        rate = float(row["value"]) if row else 13000.0
    except:
        rate = 13000.0
    return jsonify({"ok": True, "balance_usd": balance, "balance_syp": balance * rate, "rate": rate})


# ===== PRODUCTS =====

@app.route("/api/products", methods=["GET"])
def products():
    try:
        conn = get_db()
        rows = conn.execute("SELECT * FROM products WHERE active=1 ORDER BY name").fetchall()
        conn.close()
        return jsonify({"ok": True, "products": [dict(r) for r in rows]})
    except:
        return jsonify({"ok": True, "products": []})


# ===== HEALTH =====

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "Shadow Store API", "time": datetime.utcnow().isoformat()})


# ===== HELPERS =====

def _safe_user(user: dict, balance: float, orders: list) -> dict:
    return {
        "id":          user.get("id"),
        "name":        user.get("name"),
        "email":       user.get("email"),
        "phone":       user.get("phone") or "",
        "avatar_url":  user.get("avatar_url") or "",
        "telegram_id": user.get("telegram_id"),
        "created_at":  user.get("created_at"),
        "balance":     balance,
        "orders_count": len(orders),
        "orders":       orders[:10],
    }


# ===== SERVE LOGO FROM ROOT =====
@app.route("/logo.png", methods=["GET"])
def serve_logo():
    import os
    from flask import send_file
    # ابحث عن الصورة في المجلد الرئيسي أو static
    for path in ["logo.png", "static/logo.png", "logo.jpg", "logo.jpeg"]:
        if os.path.exists(path):
            return send_file(path, mimetype="image/png")
    return "", 404


if __name__ == "__main__":
    init_sessions()
    port = int(os.environ.get("API_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
