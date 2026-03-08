# app.py — Shadow Store Website API
import os, base64, requests as req
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from db import *

app = Flask(__name__)
CORS(app, origins="*")

# ── TELEGRAM NOTIFY ──
def tg_notify(msg, parse_mode="HTML"):
    try:
        token  = get_setting("bot_token","")
        admin  = get_setting("admin_tg_id","")
        if not token or not admin: return
        req.post(f"https://api.telegram.org/bot{token}/sendMessage",
                 json={"chat_id":admin,"text":msg,"parse_mode":parse_mode}, timeout=5)
    except: pass

def tg_photo(photo_url, caption):
    try:
        token = get_setting("bot_token","")
        admin = get_setting("admin_tg_id","")
        if not token or not admin: return
        req.post(f"https://api.telegram.org/bot{token}/sendPhoto",
                 json={"chat_id":admin,"photo":photo_url,"caption":caption,"parse_mode":"HTML"}, timeout=5)
    except: pass

# ── HELPERS ──
def get_uid():
    token = request.headers.get("Authorization","").replace("Bearer ","").strip()
    return verify_token(token), token

def safe_user(u):
    return {k: (str(v) if isinstance(v, datetime) else v)
            for k,v in u.items() if k != "password_hash"}

def fmt_dt(v):
    return str(v)[:16].replace("T"," ") if v else "—"

# ── STATIC ──
@app.route("/")
def index():
    if os.path.exists("index.html"): return send_file("index.html")
    return "<h1>Shadow Store</h1>", 200

@app.route("/logo.png")
def logo():
    for p in ["logo.png","static/logo.png"]:
        if os.path.exists(p): return send_file(p, mimetype="image/png")
    return "",404

@app.route("/api/health")
def health():
    return jsonify({"ok":True,"time":datetime.utcnow().isoformat()})

# ── AUTH ──
@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.get_json() or {}
    name  = (d.get("name") or "").strip()
    email = (d.get("email") or "").strip()
    phone = (d.get("phone") or "").strip()
    pw    = d.get("password","")
    if not name:  return jsonify({"ok":False,"error":"الاسم مطلوب"}),400
    if not email: return jsonify({"ok":False,"error":"البريد الإلكتروني مطلوب"}),400
    if len(pw)<6: return jsonify({"ok":False,"error":"كلمة المرور 6 أحرف على الأقل"}),400
    token, result = register_user(name, email, phone, pw)
    if not token: return jsonify({"ok":False,"error":result}),409
    tg_notify(f"👤 <b>مستخدم جديد</b>\nالاسم: {name}\nالبريد: {email}\nالهاتف: {phone or '—'}")
    return jsonify({"ok":True,"token":token,"user":safe_user(result)})

@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.get_json() or {}
    ident = (d.get("identifier") or "").strip()
    pw    = d.get("password","")
    if not ident or not pw: return jsonify({"ok":False,"error":"يرجى ملء جميع الحقول"}),400
    token, result = login_user(ident, pw)
    if not token: return jsonify({"ok":False,"error":result}),401
    return jsonify({"ok":True,"token":token,"user":safe_user(result)})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    _, token = get_uid()
    if token: logout_user(token)
    return jsonify({"ok":True})

# ── USER ──
@app.route("/api/user/me")
def me():
    uid, _ = get_uid()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),401
    u = get_user(uid)
    if not u: return jsonify({"ok":False,"error":"المستخدم غير موجود"}),404
    return jsonify({"ok":True,"user":safe_user(u)})

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

# ── WALLET ──
@app.route("/api/wallet")
def wallet():
    uid, _ = get_uid()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),401
    u = get_user(uid)
    rate = float(get_setting("usd_to_syp","13000"))
    bal  = u.get("balance",0.0) if u else 0.0
    deps = get_user_deposits(uid)
    return jsonify({"ok":True,"balance_usd":bal,"balance_syp":bal*rate,"rate":rate,"deposits":deps})

# ── DEPOSITS ──
@app.route("/api/deposit", methods=["POST"])
def deposit():
    uid, _ = get_uid()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),401
    d = request.get_json() or {}
    amount    = float(d.get("amount",0))
    method    = (d.get("method") or "").strip()
    tx_number = (d.get("tx_number") or "").strip()
    screenshot= d.get("screenshot","")  # base64 data URL

    if amount <= 0:   return jsonify({"ok":False,"error":"المبلغ غير صحيح"}),400
    if not method:    return jsonify({"ok":False,"error":"طريقة الدفع مطلوبة"}),400
    if not tx_number: return jsonify({"ok":False,"error":"رقم المعاملة مطلوب"}),400
    if not screenshot:return jsonify({"ok":False,"error":"صورة الإيصال مطلوبة"}),400

    # احفظ الصورة base64 كرابط data مؤقتاً
    dep = create_deposit(uid, amount, method, tx_number, screenshot[:200]+"...")
    if not dep: return jsonify({"ok":False,"error":"خطأ في الحفظ"}),500

    u = get_user(uid)
    rate = float(get_setting("usd_to_syp","13000"))
    syp  = int(amount * rate)

    # إشعار الأدمن
    tg_notify(
        f"💰 <b>طلب تعبئة رصيد جديد</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 المستخدم: {u['name']}\n"
        f"📧 البريد: {u['email']}\n"
        f"💵 المبلغ: <b>${amount:.2f}</b> (~{syp:,} ل.س)\n"
        f"🏦 الطريقة: {method}\n"
        f"🔢 رقم المعاملة: <code>{tx_number}</code>\n"
        f"━━━━━━━━━━━━━━\n"
        f"✅ موافقة: /dep_ok_{dep['id']}\n"
        f"❌ رفض: /dep_no_{dep['id']}"
    )
    return jsonify({"ok":True,"deposit_id":dep["id"],
                    "message":"تم إرسال طلبك، سيتم مراجعته خلال دقائق"})

# ── ORDERS ──
@app.route("/api/order", methods=["POST"])
def order():
    uid, _ = get_uid()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),401
    d = request.get_json() or {}
    game_id      = d.get("game_id","")
    game_name    = d.get("game_name","")
    product_id   = d.get("product_id","")
    product_name = d.get("product_name","")
    player_id    = (d.get("player_id") or "").strip()
    price        = float(d.get("price",0))

    if not player_id: return jsonify({"ok":False,"error":"معرف اللاعب مطلوب"}),400
    if price <= 0:    return jsonify({"ok":False,"error":"السعر غير صحيح"}),400

    ord_, err = create_order(uid, game_id, game_name, product_id, product_name, player_id, price)
    if err: return jsonify({"ok":False,"error":err}),400

    u = get_user(uid)
    rate = float(get_setting("usd_to_syp","13000"))

    # إشعار الأدمن
    tg_notify(
        f"🛒 <b>طلب شراء جديد</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 المستخدم: {u['name']}\n"
        f"📧 البريد: {u['email']}\n"
        f"🎮 اللعبة: {game_name}\n"
        f"📦 المنتج: {product_name}\n"
        f"🆔 معرف اللاعب: <code>{player_id}</code>\n"
        f"💵 السعر: <b>${price:.2f}</b>\n"
        f"💰 الرصيد المتبقي: ${u['balance']:.2f}\n"
        f"━━━━━━━━━━━━━━\n"
        f"✅ إتمام: /ord_ok_{ord_['id']}\n"
        f"🔄 استرداد: /ord_ref_{ord_['id']}"
    )
    return jsonify({"ok":True,"order":ord_,
                    "message":"تم استلام طلبك وجاري التنفيذ"})

@app.route("/api/orders")
def orders():
    uid, _ = get_uid()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),401
    ords = get_user_orders(uid)
    return jsonify({"ok":True,"orders":ords})

# ── SETTINGS (public) ──
@app.route("/api/settings/payment")
def payment_settings():
    return jsonify({
        "ok": True,
        "shamcash":  get_setting("shamcash_number","09XXXXXXXX"),
        "syriatel":  get_setting("syriatel_number","09XXXXXXXX"),
        "rate":      float(get_setting("usd_to_syp","13000")),
    })

# ── ADMIN ──
def require_admin():
    uid, _ = get_uid()
    if not uid: return None
    u = get_user(uid)
    return uid if u and u.get("is_admin") else None

@app.route("/api/admin/deposits")
def admin_deposits():
    uid = require_admin()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),403
    return jsonify({"ok":True,"deposits":get_pending_deposits()})

@app.route("/api/admin/orders")
def admin_orders():
    uid = require_admin()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),403
    return jsonify({"ok":True,"orders":get_pending_orders()})

@app.route("/api/admin/deposit/approve", methods=["POST"])
def admin_dep_approve():
    uid = require_admin()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),403
    d = request.get_json() or {}
    ok, dep = approve_deposit(d.get("id"), d.get("note",""))
    if not ok: return jsonify({"ok":False,"error":str(dep)}),400
    u = get_user(dep["user_id"])
    tg_notify(f"✅ تمت الموافقة على تعبئة رصيد\n👤 {u['name']}\n💵 ${dep['amount']:.2f}\n💰 الرصيد الجديد: ${u['balance']:.2f}")
    return jsonify({"ok":True})

@app.route("/api/admin/deposit/reject", methods=["POST"])
def admin_dep_reject():
    uid = require_admin()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),403
    d = request.get_json() or {}
    ok = reject_deposit(d.get("id"), d.get("reason",""))
    return jsonify({"ok":ok})

@app.route("/api/admin/order/complete", methods=["POST"])
def admin_ord_complete():
    uid = require_admin()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),403
    d = request.get_json() or {}
    ord_ = complete_order(d.get("id"), d.get("note",""))
    if not ord_: return jsonify({"ok":False,"error":"الطلب غير موجود"}),400
    return jsonify({"ok":True})

@app.route("/api/admin/order/refund", methods=["POST"])
def admin_ord_refund():
    uid = require_admin()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),403
    d = request.get_json() or {}
    ok = refund_order(d.get("id"), d.get("reason",""))
    return jsonify({"ok":ok})

@app.route("/api/admin/users")
def admin_users():
    uid = require_admin()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),403
    return jsonify({"ok":True,"users":get_all_users()})

@app.route("/api/admin/balance", methods=["POST"])
def admin_balance():
    uid = require_admin()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),403
    d = request.get_json() or {}
    admin_set_balance(d["user_id"], float(d["amount"]))
    return jsonify({"ok":True})

@app.route("/api/admin/settings", methods=["POST"])
def admin_settings():
    uid = require_admin()
    if not uid: return jsonify({"ok":False,"error":"غير مصرح"}),403
    d = request.get_json() or {}
    for k,v in d.items():
        set_setting(k, str(v))
    return jsonify({"ok":True})

if __name__ == "__main__":
    init_tables()
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port, debug=False)
