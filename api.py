# api.py — Shadow Store REST API (PostgreSQL / Supabase)
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pg_db import (
    init_web_tables, register_user, login_user,
    verify_token, logout_user, get_user_by_id,
    update_user, get_bot_balance, get_bot_orders,
    get_exchange_rate, link_telegram
)

app = Flask(__name__)
CORS(app, origins="*")

def safe_user(user: dict, balance=None, orders=None) -> dict:
    tg_id = user.get("telegram_id")
    bal   = balance if balance is not None else get_bot_balance(tg_id)
    ords  = orders  if orders  is not None else get_bot_orders(tg_id)
    return {
        "id":           user.get("id"),
        "name":         user.get("name",""),
        "email":        user.get("email",""),
        "phone":        user.get("phone") or "",
        "avatar_url":   user.get("avatar_url") or "",
        "telegram_id":  tg_id,
        "created_at":   str(user.get("created_at","")),
        "balance":      bal,
        "orders_count": len(ords),
        "orders":       ords[:15],
    }

def get_uid():
    token = request.headers.get("Authorization","").replace("Bearer ","").strip()
    return verify_token(token), token

@app.route("/", methods=["GET"])
def index():
    for p in ["index.html","store-customer.html"]:
        if os.path.exists(p):
            return send_file(p)
    return "<h1 style='color:#fff;background:#04060f;padding:40px;text-align:center'>🌑 Shadow Store</h1>",200

@app.route("/logo.png")
def logo():
    for p in ["logo.png","static/logo.png"]:
        if os.path.exists(p):
            return send_file(p, mimetype="image/png")
    return "",404

@app.route("/api/health")
def health():
    return jsonify({"ok":True,"time":datetime.utcnow().isoformat()})

@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.get_json() or {}
    name  = (d.get("name") or "").strip()
    email = (d.get("email") or "").strip()
    phone = (d.get("phone") or "").strip()
    pw    = d.get("password") or ""
    if not name:  return jsonify({"ok":False,"error":"الاسم مطلوب"}),400
    if not email: return jsonify({"ok":False,"error":"البريد الإلكتروني مطلوب"}),400
    if len(pw)<6: return jsonify({"ok":False,"error":"كلمة المرور 6 أحرف على الأقل"}),400
    token, result = register_user(name, email, phone, pw)
    if not token:
        return jsonify({"ok":False,"error":result}),409
    return jsonify({"ok":True,"token":token,"user":safe_user(result,0.0,[])})

@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.get_json() or {}
    ident = (d.get("identifier") or "").strip()
    pw    = d.get("password") or ""
    if not ident or not pw:
        return jsonify({"ok":False,"error":"يرجى ملء جميع الحقول"}),400
    token, result = login_user(ident, pw)
    if not token:
        return jsonify({"ok":False,"error":result}),401
    return jsonify({"ok":True,"token":token,"user":safe_user(result)})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    uid, token = get_uid()
    if token: logout_user(token)
    return jsonify({"ok":True})

@app.route("/api/user/me", methods=["GET"])
def me():
    uid, _ = get_uid()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),401
    user = get_user_by_id(uid)
    if not user: return jsonify({"ok":False,"error":"المستخدم غير موجود"}),404
    return jsonify({"ok":True,"user":safe_user(user)})

@app.route("/api/user/update", methods=["POST"])
def update():
    uid, _ = get_uid()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),401
    d = request.get_json() or {}
    fields = {}
    if d.get("name"):     fields["name"]     = d["name"].strip()
    if d.get("email"):    fields["email"]    = d["email"].strip()
    if "phone" in d:      fields["phone"]    = (d["phone"] or "").strip() or None
    if d.get("password"): fields["password"] = d["password"]
    if not fields: return jsonify({"ok":False,"error":"لا توجد بيانات"}),400
    if "password" in fields and len(fields["password"])<6:
        return jsonify({"ok":False,"error":"كلمة المرور قصيرة"}),400
    user, err = update_user(uid, **fields)
    if err: return jsonify({"ok":False,"error":err}),409
    return jsonify({"ok":True,"user":safe_user(user)})

@app.route("/api/user/link-telegram", methods=["POST"])
def link_tg():
    uid, _ = get_uid()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),401
    tg_id = (request.get_json() or {}).get("telegram_id")
    if not tg_id: return jsonify({"ok":False,"error":"معرف تيليغرام مطلوب"}),400
    ok, err = link_telegram(uid, tg_id)
    if not ok: return jsonify({"ok":False,"error":err}),409
    return jsonify({"ok":True,"user":safe_user(get_user_by_id(uid))})

@app.route("/api/orders")
def orders():
    uid, _ = get_uid()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),401
    user = get_user_by_id(uid)
    tg_id = user.get("telegram_id") if user else None
    return jsonify({"ok":True,"orders":get_bot_orders(tg_id)})

@app.route("/api/wallet")
def wallet():
    uid, _ = get_uid()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),401
    user = get_user_by_id(uid)
    tg_id = user.get("telegram_id") if user else None
    bal  = get_bot_balance(tg_id)
    rate = get_exchange_rate()
    return jsonify({"ok":True,"balance_usd":bal,"balance_syp":bal*rate,"rate":rate})

if __name__ == "__main__":
    init_web_tables()
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port, debug=False)
