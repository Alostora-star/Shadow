# populate_db.py - النسخة الصحيحة النهائية
# تستخدم init_db() من database.py مباشرة لضمان تطابق الهيكل 100%
import asyncio
import os
import sys

# إضافة المسار الحالي للاستيراد
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_db,
    add_product_db,
)
import sqlite3

DB_PATH = 'bot_data.db'

def add_categories_and_subcategories(conn):
    """إضافة الفئات والفئات الفرعية مباشرة عبر SQL."""
    cursor = conn.cursor()

    # الفئات الرئيسية
    categories = [
        ('cat_games',       'الألعاب',           'باقات شحن الألعاب',    '🎮', 1),
        ('cat_activations', 'أرقام التفعيلات',   'أرقام تفعيل الحسابات', '📱', 2),
    ]
    for cat in categories:
        try:
            cursor.execute(
                'INSERT INTO categories (category_id, name, description, icon, display_order) VALUES (?, ?, ?, ?, ?)',
                cat
            )
        except sqlite3.IntegrityError:
            pass  # موجود مسبقاً

    # الفئات الفرعية
    subcategories = [
        ('game_freefire',     'cat_games',       'فري فاير (Free Fire)', 'شحن جواهر فري فاير',   '🔥', 1),
        ('game_pubg',         'cat_games',       'ببجي (PUBG)',           'شحن UC ببجي',           '🎯', 2),
        ('game_jawaker',      'cat_games',       'JAWAKER',               'شحن جواكر',             '♣️', 3),
        ('game_fcmobile',     'cat_games',       'FC Mobile',             'شحن FC Mobile',         '🪙', 4),
        ('game_cod',          'cat_games',       'Call of Duty',          'شحن COD',               '🔫', 5),
        ('game_wildrift',     'cat_games',       'Wild Rift',             'شحن Wild Core',         '🌊', 6),
        ('game_aoe',          'cat_games',       'Age Of Empires',        'شحن Age Of Empires',    '🏰', 7),
        ('game_hok',          'cat_games',       'Honor of Kings',        'شحن Honor of Kings',    '🤴', 8),
        ('game_lordsmobile',  'cat_games',       'Lords Mobile',          'شحن Lords Mobile',      '🛡️', 9),
        ('game_genshin',      'cat_games',       'GENSHIN IMPACT',        'شحن Genesis Crystals',  '✨', 10),
        ('game_mobilelegends','cat_games',       'Mobile Legends',        'شحن Diamonds MLBB',     '😁', 11),
        ('act_telegram',      'cat_activations', 'تليجرام (Telegram)',    'رقم تفعيل تليجرام',    '🔹', 1),
        ('act_whatsapp',      'cat_activations', 'واتساب (WhatsApp)',     'رقم تفعيل واتساب',     '🔹', 2),
        ('act_apple',         'cat_activations', 'Apple ID',              'رقم تفعيل Apple ID',   '🔹', 3),
        ('act_google',        'cat_activations', 'حساب Google',           'رقم تفعيل Google',     '🔹', 4),
    ]
    for sub in subcategories:
        try:
            cursor.execute(
                'INSERT INTO subcategories (subcategory_id, category_id, name, description, icon, display_order) VALUES (?, ?, ?, ?, ?, ?)',
                sub
            )
        except sqlite3.IntegrityError:
            pass

    conn.commit()

async def populate():
    # حذف قاعدة البيانات القديمة
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("تم حذف قاعدة البيانات القديمة...")

    # إنشاء الجداول بنفس هيكل database.py (init_db يستخدم DATABASE_NAME من config)
    init_db()
    print("✅ تم إنشاء الجداول بهيكل database.py الصحيح")

    # إضافة الفئات والفئات الفرعية
    conn = sqlite3.connect(DB_PATH)
    add_categories_and_subcategories(conn)
    conn.close()
    print("✅ تم إضافة الفئات والفئات الفرعية")

    # ===== إضافة المنتجات عبر add_product_db =====
    # (product_id, name, price, category_id, subcategory_id, server_id, description, icon, requires_game_id, display_order)

    # فري فاير - product_id = ما بعد "buy_freefire_"
    ff = [
        ('100',  '100 💎 الماسة - فري فاير',   1.00, 'cat_games', 'game_freefire',  None, 'شحن 100 جوهرة فري فاير',   '💎', 1, 1),
        ('210',  '210 💎 الماسة - فري فاير',   2.00, 'cat_games', 'game_freefire',  None, 'شحن 210 جوهرة فري فاير',   '💎', 1, 2),
        ('520',  '520 💎 الماسة - فري فاير',   5.00, 'cat_games', 'game_freefire',  None, 'شحن 520 جوهرة فري فاير',   '💎', 1, 3),
        ('1080', '1080 💎 الماسة - فري فاير',  10.00, 'cat_games', 'game_freefire',  None, 'شحن 1080 جوهرة فري فاير',  '💎', 1, 4),
    ]

    # ببجي - product_id = "pubg_" + ما بعد "buy_pubg_"
    pubg = [
        ('pubg_60',  '60 💸 UC - ببجي',   0.95, 'cat_games', 'game_pubg', None, 'شحن 60 UC ببجي',   '💸', 1, 1),
        ('pubg_120', '120 💸 UC - ببجي',  1.90, 'cat_games', 'game_pubg', None, 'شحن 120 UC ببجي',  '💸', 1, 2),
        ('pubg_325', '325 💸 UC - ببجي',  4.70, 'cat_games', 'game_pubg', None, 'شحن 325 UC ببجي',  '💸', 1, 3),
    ]

    # جواكر - product_id = ما بعد "buy_jawaker_"
    jawaker = [
        ('10000', '10000 ♣️ - جواكر',    1.50,  'cat_games', 'game_jawaker', None, 'شحن 10000 جواكر',  '♣️', 1, 1),
        ('red',   'مسرع الاحمر ♦️',      2.00,  'cat_games', 'game_jawaker', None, 'مسرع احمر جواكر',  '♦️', 1, 2),
        ('black', 'مسرع اسود ♣️',       17.00,  'cat_games', 'game_jawaker', None, 'مسرع اسود جواكر',  '♣️', 1, 3),
        ('blue',  'مسرع ازرق 🏄',        9.00,  'cat_games', 'game_jawaker', None, 'مسرع ازرق جواكر',  '🏄', 1, 4),
    ]

    # FC Mobile - product_id = ما بعد "buy_fcmobile_"
    fcm = [
        ('99s',   '99 🥈 - FC Mobile',         1.50,  'cat_games', 'game_fcmobile', None, 'شحن 99 فضة',     '🥈', 1, 1),
        ('499s',  '499 🥈 - FC Mobile',        7.50,  'cat_games', 'game_fcmobile', None, 'شحن 499 فضة',    '🥈', 1, 2),
        ('999s',  '999 🥈 - FC Mobile',       14.00,  'cat_games', 'game_fcmobile', None, 'شحن 999 فضة',    '🥈', 1, 3),
        ('100p',  '100 point 🪙 - FC Mobile',  1.50,  'cat_games', 'game_fcmobile', None, 'شحن 100 نقطة',   '🪙', 1, 4),
        ('500p',  '500 point 🪙 - FC Mobile',  7.50,  'cat_games', 'game_fcmobile', None, 'شحن 500 نقطة',   '🪙', 1, 5),
        ('1070p', '1070 point 🪙 - FC Mobile',14.00,  'cat_games', 'game_fcmobile', None, 'شحن 1070 نقطة',  '🪙', 1, 6),
    ]

    # Call of Duty - product_id = ما بعد "buy_cod_"
    cod = [
        ('88',  '88 🪙 - Call of Duty',             1.50, 'cat_games', 'game_cod', None, 'شحن 88 COD Points',   '🪙', 1, 1),
        ('460', '460 🪙 - Call of Duty',            7.00, 'cat_games', 'game_cod', None, 'شحن 460 COD Points',  '🪙', 1, 2),
        ('bp',  'Battle Pass 💎💫 - COD',           3.50, 'cat_games', 'game_cod', None, 'Battle Pass',          '💎', 1, 3),
        ('bpb', 'Battle Pass Bundle 💪 - COD',      8.00, 'cat_games', 'game_cod', None, 'Battle Pass Bundle',   '💪', 1, 4),
    ]

    # Wild Rift - product_id = ما بعد "buy_wildrift_"
    wr = [
        ('425',   '425 🪙 - Wild Rift',       6.00,  'cat_games', 'game_wildrift', None, 'شحن 425 Wild Core',  '🪙', 1, 1),
        ('stella','STELLA CORN - Wild Rift',  6.50,  'cat_games', 'game_wildrift', None, 'STELLA CORN',        '🌟', 1, 2),
        ('1000',  '1000 🪙 - Wild Rift',     14.00,  'cat_games', 'game_wildrift', None, 'شحن 1000 Wild Core', '🪙', 1, 3),
    ]

    # Age Of Empires - product_id = "aoe_" + ما بعد "buy_aoe_"
    aoe = [
        ('aoe_99',  '99 🪙 - Age Of Empires',    1.30,  'cat_games', 'game_aoe', None, 'شحن 99',   '🏰', 1, 1),
        ('aoe_499', '499 🪙 - Age Of Empires',   6.50,  'cat_games', 'game_aoe', None, 'شحن 499',  '🏰', 1, 2),
        ('aoe_999', '999 🪙 - Age Of Empires',  12.50,  'cat_games', 'game_aoe', None, 'شحن 999',  '🏰', 1, 3),
    ]

    # Honor of Kings - product_id = ما بعد "buy_hok_"
    hok = [
        ('400', '400 💸 - Honor of Kings',   6.00, 'cat_games', 'game_hok', None, 'شحن 400', '💸', 1, 1),
        ('800', '800 💸 - Honor of Kings',  12.00, 'cat_games', 'game_hok', None, 'شحن 800', '💸', 1, 2),
    ]

    # Lords Mobile - product_id = ما بعد "buy_lordsmobile_"
    lords = [
        ('195',     '195 💎 - Lords Mobile',           2.50,  'cat_games', 'game_lordsmobile', None, 'شحن 195',        '💎', 1, 1),
        ('395',     '395 💎 - Lords Mobile',           6.50,  'cat_games', 'game_lordsmobile', None, 'شحن 395',        '💎', 1, 2),
        ('785',     '785 💎 - Lords Mobile',          11.00,  'cat_games', 'game_lordsmobile', None, 'شحن 785',        '💎', 1, 3),
        ('weekly',  'اشتراك أسبوعي 💎 - Lords Mobile', 2.50, 'cat_games', 'game_lordsmobile', None, 'اشتراك أسبوعي', '💎', 1, 4),
        ('monthly', 'اشتراك شهري 💎 - Lords Mobile',  27.00, 'cat_games', 'game_lordsmobile', None, 'اشتراك شهري',   '💎', 1, 5),
    ]

    # Genshin Impact - product_id = "genshin_" + ما بعد "buy_genshin_" (عدا moon)
    genshin = [
        ('genshin_60',   '60 🔮 - Genshin Impact',          1.00,  'cat_games', 'game_genshin', None, 'شحن 60 Genesis Crystals',       '🔮', 1, 1),
        ('genshin_330',  '330 🔮 - Genshin Impact',         5.00,  'cat_games', 'game_genshin', None, 'شحن 330 Genesis Crystals',      '🔮', 1, 2),
        ('moon',         'Welkin Moon 🌙 - Genshin Impact', 5.00,  'cat_games', 'game_genshin', None, 'Blessing of the Welkin Moon',   '🌙', 1, 3),
        ('genshin_1090', '1090 🔮 - Genshin Impact',       16.00,  'cat_games', 'game_genshin', None, 'شحن 1090 Genesis Crystals',     '🔮', 1, 4),
    ]

    # Mobile Legends - product_id = ما بعد "buy_mobilelegends_"
    ml = [
        ('56',         '56 💎 - Mobile Legends',           1.40,  'cat_games', 'game_mobilelegends', None, 'شحن 56 Diamonds',     '💎', 1, 1),
        ('86',         '86 💎 - Mobile Legends',           1.80,  'cat_games', 'game_mobilelegends', None, 'شحن 86 Diamonds',     '💎', 1, 2),
        ('170',        '170 💎 - Mobile Legends',          3.50,  'cat_games', 'game_mobilelegends', None, 'شحن 170 Diamonds',    '💎', 1, 3),
        ('255',        '255 💎 - Mobile Legends',          6.00,  'cat_games', 'game_mobilelegends', None, 'شحن 255 Diamonds',    '💎', 1, 4),
        ('weeklypass', 'Weekly Diamond Pass 💎 - MLBB',    2.60,  'cat_games', 'game_mobilelegends', None, 'Weekly Diamond Pass', '💎', 1, 5),
        ('twilight',   'Twilight Pass ✨ 💎 - MLBB',      11.00,  'cat_games', 'game_mobilelegends', None, 'Twilight Pass',       '✨', 1, 6),
    ]

    # أرقام التفعيلات - requires_game_id=0 (لا تحتاج معرف لعبة)
    act = [
        ('prod_tg',     'رقم تفعيل تليجرام',      1.50, 'cat_activations', 'act_telegram', None, 'رقم تفعيل تليجرام',      '✈️', 0, 1),
        ('prod_wa',     'رقم تفعيل واتساب',        2.00, 'cat_activations', 'act_whatsapp', None, 'رقم تفعيل واتساب',        '💬', 0, 2),
        ('prod_apple',  'رقم تفعيل Apple ID',      3.00, 'cat_activations', 'act_apple',    None, 'رقم تفعيل Apple ID',      '🍎', 0, 3),
        ('prod_google', 'رقم تفعيل حساب Google',   1.80, 'cat_activations', 'act_google',   None, 'رقم تفعيل حساب Google',   '📧', 0, 4),
    ]

    # إدراج جميع المنتجات
    all_products = ff + pubg + jawaker + fcm + cod + wr + aoe + hok + lords + genshin + ml + act
    count = 0
    for p in all_products:
        pid, name, price, cat_id, subcat_id, srv_id, desc, icon, req_id, order = p
        result = await add_product_db(pid, name, price, cat_id, subcat_id, srv_id, desc, icon, req_id, order)
        if result:
            count += 1

    print(f"\n✅ تم ملء قاعدة البيانات بنجاح!")
    print(f"   🔥 فري فاير:         4 منتجات")
    print(f"   🎯 ببجي:             3 منتجات")
    print(f"   ♣️  جواكر:            4 منتجات")
    print(f"   🪙 FC Mobile:        6 منتجات")
    print(f"   🔫 Call of Duty:     4 منتجات")
    print(f"   🌊 Wild Rift:        3 منتجات")
    print(f"   🏰 Age Of Empires:   3 منتجات")
    print(f"   🤴 Honor of Kings:   2 منتجات")
    print(f"   🛡️  Lords Mobile:     5 منتجات")
    print(f"   ✨ Genshin Impact:   4 منتجات")
    print(f"   😁 Mobile Legends:   6 منتجات")
    print(f"   📱 أرقام التفعيلات:  4 منتجات")
    print(f"   ─────────────────────────────")
    print(f"   📦 تم إدراج {count} منتجاً من أصل {len(all_products)}")

if __name__ == '__main__':
    asyncio.run(populate())