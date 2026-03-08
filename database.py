# database.py
import os
import logging
from datetime import datetime, timedelta
import uuid

# ===== DATABASE BACKEND =====
# إذا كان DATABASE_URL موجوداً يستخدم PostgreSQL، وإلا SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

    def sqlite3_connect(name=None):
        """محاكاة sqlite3.connect باستخدام psycopg2"""
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn

    class FakeModule:
        """محاكاة وحدة sqlite3"""
        connect = staticmethod(sqlite3_connect)
        class Row: pass
        OperationalError = psycopg2.OperationalError
        IntegrityError = psycopg2.IntegrityError

    import sqlite3 as _sqlite3_orig
    sqlite3 = FakeModule()

    # تعديل الـ placeholders من ? إلى %s
    def _fix_query(q):
        return q.replace("?", "%s")

    # نعيد تعريف connect لتصحيح الـ queries تلقائياً
    _orig_connect = sqlite3_connect
    def _pg_connect(name=None):
        conn = _orig_connect(name)
        orig_execute = conn.cursor().__class__.execute
        class PatchedCursor(psycopg2.extras.RealDictCursor):
            def execute(self, query, params=None):
                return super().execute(_fix_query(query), params)
            def executemany(self, query, params=None):
                return super().executemany(_fix_query(query), params)
        conn2 = psycopg2.connect(DATABASE_URL, cursor_factory=PatchedCursor)
        conn2.autocommit = False
        return conn2
    sqlite3.connect = staticmethod(_pg_connect)

    DATABASE_NAME = DATABASE_URL
    print("✅ PostgreSQL mode (Supabase)")
else:
    import sqlite3
    from config import DATABASE_NAME
    print("⚠️ SQLite mode (local)")

logger = logging.getLogger(__name__)

def init_db():
    """Initializes the database by creating necessary tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # جدول المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0.0,
            currency TEXT DEFAULT 'USD',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_activity TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # جدول الإعدادات العامة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # إدراج سعر الصرف الافتراضي إن لم يكن موجوداً
    cursor.execute("""
        INSERT OR IGNORE INTO settings (key, value) VALUES ('usd_to_syp', '12000')
    """)

    # جدول معرفات الألعاب المحفوظة (ميزة جديدة)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_game_ids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_name TEXT,
            game_id TEXT,
            is_default INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # جدول الفئات (جديد)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            display_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # جدول الفئات الفرعية (جديد)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subcategory_id TEXT UNIQUE,
            category_id TEXT,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            display_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    """)

    # جدول السيرفرات (جديد)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id TEXT UNIQUE,
            subcategory_id TEXT,
            name TEXT NOT NULL,
            description TEXT,
            availability_start_hour INTEGER,
            availability_end_hour INTEGER,
            display_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(subcategory_id)
        )
    """)

    # جدول المنتجات (جديد)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category_id TEXT,
            subcategory_id TEXT,
            server_id TEXT,
            icon TEXT,
            display_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            requires_game_id INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(category_id),
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(subcategory_id),
            FOREIGN KEY (server_id) REFERENCES servers(server_id)
        )
    """)

    # جدول المدفوعات المعلقة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_payments (
            payment_id TEXT PRIMARY KEY,
            user_id INTEGER,
            username TEXT,
            amount REAL,
            transaction_id TEXT,
            payment_method TEXT,
            status TEXT,
            timestamp TEXT
        )
    """)

    # جدول سلة المشتريات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_carts (
            user_id INTEGER,
            product_id TEXT,
            product_name TEXT,
            price REAL,
            quantity INTEGER DEFAULT 1,
            timestamp TEXT,
            PRIMARY KEY (user_id, product_id)
        )
    """)

    # جدول سجل المشتريات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases_history (
            purchase_id TEXT PRIMARY KEY,
            user_id INTEGER,
            username TEXT,
            product_name TEXT,
            game_id TEXT,
            price REAL,
            status TEXT,
            timestamp TEXT,
            shipped_at TEXT
        )
    """)
    
    # جدول الكوبونات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_type TEXT NOT NULL,
            discount_value REAL NOT NULL,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

# --- دوال إدارة الفئات ---

async def add_category_db(category_id: str, name: str, description: str = None, icon: str = None, display_order: int = 0):
    """إضافة فئة جديدة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO categories (category_id, name, description, icon, display_order)
            VALUES (?, ?, ?, ?, ?)
        """, (category_id, name, description, icon, display_order))
        conn.commit()
        logger.info(f"Category added: {name}")
        return True
    except sqlite3.IntegrityError:
        logger.error(f"Category with ID {category_id} already exists.")
        return False
    finally:
        conn.close()

async def get_all_categories_db(active_only: bool = True):
    """جلب جميع الفئات."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY display_order, name")
    else:
        cursor.execute("SELECT * FROM categories ORDER BY display_order, name")
    results = cursor.fetchall()
    conn.close()
    
    categories = []
    keys = ["id", "category_id", "name", "description", "icon", "display_order", "is_active", "created_at"]
    for row in results:
        categories.append(dict(zip(keys, row)))
    return categories

async def update_category_db(category_id: str, **kwargs):
    """تحديث بيانات فئة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    allowed_fields = ["name", "description", "icon", "display_order", "is_active"]
    updates = []
    values = []
    
    for field, value in kwargs.items():
        if field in allowed_fields:
            updates.append(f"{field} = ?")
            values.append(value)
    
    if not updates:
        conn.close()
        return False
    
    values.append(category_id)
    query = f"UPDATE categories SET {', '.join(updates)} WHERE category_id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    logger.info(f"Category {category_id} updated.")
    return True

async def delete_category_db(category_id: str):
    """حذف فئة (soft delete)."""
    return await update_category_db(category_id, is_active=0)

# --- دوال إدارة الفئات الفرعية ---

async def add_subcategory_db(subcategory_id: str, category_id: str, name: str, description: str = None, icon: str = None, display_order: int = 0):
    """إضافة فئة فرعية جديدة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO subcategories (subcategory_id, category_id, name, description, icon, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (subcategory_id, category_id, name, description, icon, display_order))
        conn.commit()
        logger.info(f"Subcategory added: {name}")
        return True
    except sqlite3.IntegrityError:
        logger.error(f"Subcategory with ID {subcategory_id} already exists.")
        return False
    finally:
        conn.close()

async def get_subcategories_by_category_db(category_id: str, active_only: bool = True):
    """جلب الفئات الفرعية لفئة معينة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM subcategories WHERE category_id = ? AND is_active = 1 ORDER BY display_order, name", (category_id,))
    else:
        cursor.execute("SELECT * FROM subcategories WHERE category_id = ? ORDER BY display_order, name", (category_id,))
    results = cursor.fetchall()
    conn.close()
    
    subcategories = []
    keys = ["id", "subcategory_id", "category_id", "name", "description", "icon", "display_order", "is_active", "created_at"]
    for row in results:
        subcategories.append(dict(zip(keys, row)))
    return subcategories

# --- دوال إدارة السيرفرات ---

async def add_server_db(server_id: str, subcategory_id: str, name: str, description: str = None, 
                        availability_start_hour: int = None, availability_end_hour: int = None, display_order: int = 0):
    """إضافة سيرفر جديد."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO servers (server_id, subcategory_id, name, description, availability_start_hour, availability_end_hour, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (server_id, subcategory_id, name, description, availability_start_hour, availability_end_hour, display_order))
        conn.commit()
        logger.info(f"Server added: {name}")
        return True
    except sqlite3.IntegrityError:
        logger.error(f"Server with ID {server_id} already exists.")
        return False
    finally:
        conn.close()

async def get_servers_by_subcategory_db(subcategory_id: str, active_only: bool = True):
    """جلب السيرفرات لفئة فرعية معينة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM servers WHERE subcategory_id = ? AND is_active = 1 ORDER BY display_order, name", (subcategory_id,))
    else:
        cursor.execute("SELECT * FROM servers WHERE subcategory_id = ? ORDER BY display_order, name", (subcategory_id,))
    results = cursor.fetchall()
    conn.close()
    
    servers = []
    keys = ["id", "server_id", "subcategory_id", "name", "description", "availability_start_hour", "availability_end_hour", "display_order", "is_active", "created_at"]
    for row in results:
        servers.append(dict(zip(keys, row)))
    return servers

# --- دوال إدارة المنتجات ---

async def add_product_db(product_id: str, name: str, price: float, category_id: str = None, 
                        subcategory_id: str = None, server_id: str = None, description: str = None, 
                        icon: str = None, requires_game_id: int = 0, display_order: int = 0):
    """إضافة منتج جديد."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO products (product_id, name, description, price, category_id, subcategory_id, server_id, icon, requires_game_id, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, name, description, price, category_id, subcategory_id, server_id, icon, requires_game_id, display_order))
        conn.commit()
        logger.info(f"Product added: {name}")
        return True
    except sqlite3.IntegrityError:
        logger.error(f"Product with ID {product_id} already exists.")
        return False
    finally:
        conn.close()

async def get_products_by_parent_db(parent_id: str, parent_type: str, active_only: bool = True):
    """جلب المنتجات حسب الفئة أو الفئة الفرعية أو السيرفر."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    if parent_type == "category":
        field = "category_id"
    elif parent_type == "subcategory":
        field = "subcategory_id"
    elif parent_type == "server":
        field = "server_id"
    else:
        conn.close()
        return []
    
    if active_only:
        cursor.execute(f"SELECT * FROM products WHERE {field} = ? AND is_active = 1 ORDER BY display_order, name", (parent_id,))
    else:
        cursor.execute(f"SELECT * FROM products WHERE {field} = ? ORDER BY display_order, name", (parent_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    products = []
    keys = ["id", "product_id", "name", "description", "price", "category_id", "subcategory_id", "server_id", "icon", "display_order", "is_active", "requires_game_id", "created_at"]
    for row in results:
        products.append(dict(zip(keys, row)))
    return products

async def get_product_by_id_db(product_id: str):
    """جلب منتج بواسطة معرفه."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        keys = ["id", "product_id", "name", "description", "price", "category_id", "subcategory_id", "server_id", "icon", "display_order", "is_active", "requires_game_id", "created_at"]
        return dict(zip(keys, result))
    return None

async def update_product_db(product_id: str, **kwargs):
    """تحديث بيانات منتج."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    allowed_fields = ["name", "description", "price", "icon", "display_order", "is_active", "requires_game_id"]
    updates = []
    values = []
    
    for field, value in kwargs.items():
        if field in allowed_fields:
            updates.append(f"{field} = ?")
            values.append(value)
    
    if not updates:
        conn.close()
        return False
    
    values.append(product_id)
    query = f"UPDATE products SET {', '.join(updates)} WHERE product_id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    logger.info(f"Product {product_id} updated.")
    return True

async def delete_product_db(product_id: str):
    """حذف منتج (soft delete)."""
    return await update_product_db(product_id, is_active=0)

# --- دوال معرفات الألعاب المحفوظة (ميزة جديدة) ---

async def save_game_id_db(user_id: int, game_name: str, game_id: str, is_default: bool = False):
    """حفظ معرف لعبة للمستخدم."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # إذا كان هذا المعرف الافتراضي، إزالة الافتراضية من المعرفات الأخرى
    if is_default:
        cursor.execute("UPDATE saved_game_ids SET is_default = 0 WHERE user_id = ? AND game_name = ?", (user_id, game_name))
    
    cursor.execute("""
        INSERT INTO saved_game_ids (user_id, game_name, game_id, is_default)
        VALUES (?, ?, ?, ?)
    """, (user_id, game_name, game_id, 1 if is_default else 0))
    
    conn.commit()
    conn.close()
    logger.info(f"Game ID saved for user {user_id}: {game_name} - {game_id}")

async def get_saved_game_ids_db(user_id: int, game_name: str = None):
    """جلب معرفات الألعاب المحفوظة للمستخدم."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    if game_name:
        cursor.execute("SELECT * FROM saved_game_ids WHERE user_id = ? AND game_name = ? ORDER BY is_default DESC, created_at DESC", (user_id, game_name))
    else:
        cursor.execute("SELECT * FROM saved_game_ids WHERE user_id = ? ORDER BY game_name, is_default DESC, created_at DESC", (user_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    game_ids = []
    keys = ["id", "user_id", "game_name", "game_id", "is_default", "created_at"]
    for row in results:
        game_ids.append(dict(zip(keys, row)))
    return game_ids

async def delete_saved_game_id_db(user_id: int, game_id_record_id: int):
    """حذف معرف لعبة محفوظ."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_game_ids WHERE id = ? AND user_id = ?", (game_id_record_id, user_id))
    conn.commit()
    conn.close()
    logger.info(f"Game ID record {game_id_record_id} deleted for user {user_id}")

# --- دوال سلة المشتريات ---

async def add_to_cart_db(user_id: int, product_id: str, product_name: str, price: float, icon: str = None):
    """إضافة منتج إلى سلة المشتريات."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    cursor.execute("SELECT quantity FROM user_carts WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    result = cursor.fetchone()

    if result:
        cursor.execute("DELETE FROM user_carts WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        cursor.execute("""
            INSERT INTO user_carts (user_id, product_id, product_name, price, quantity, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, product_id, product_name, price, 1, timestamp))
        logger.info(f"User {user_id} updated cart item: {product_name}")
    else:
        cursor.execute("""
            INSERT INTO user_carts (user_id, product_id, product_name, price, quantity, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, product_id, product_name, price, 1, timestamp))
        logger.info(f"User {user_id} added to cart: {product_name}")

    conn.commit()
    conn.close()

async def get_user_cart_db(user_id: int):
    """جلب محتويات سلة المشتريات."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, product_name, price, quantity FROM user_carts WHERE user_id = ?", (user_id,))
    results = cursor.fetchall()
    conn.close()

    cart = []
    for row in results:
        cart.append({
            "product_id": row[0],
            "product_name": row[1],
            "price": row[2],
            "quantity": row[3]
        })
    return cart

async def clear_user_cart_db(user_id: int):
    """مسح سلة المشتريات."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_carts WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    logger.info(f"User {user_id} cart cleared.")

async def remove_from_cart_db(user_id: int, product_id: str):
    """حذف منتج من السلة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_carts WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    conn.commit()
    conn.close()
    logger.info(f"User {user_id} removed item {product_id} from cart.")

# --- دوال المحفظة ---

async def get_user_wallet_db(user_id: int) -> float:
    """جلب رصيد المحفظة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return 0.0

async def update_user_wallet_db(user_id: int, amount: float, username: str = None):
    """تحديث رصيد المحفظة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    current_time = datetime.now().isoformat()

    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        new_balance = existing_user[0] + amount
        cursor.execute("UPDATE users SET balance = ?, last_activity = ? WHERE user_id = ?", (new_balance, current_time, user_id))
    else:
        new_balance = amount
        if username:
             cursor.execute("INSERT INTO users (user_id, username, balance, created_at, last_activity) VALUES (?, ?, ?, ?, ?)", (user_id, username, new_balance, current_time, current_time))
        else:
             cursor.execute("INSERT INTO users (user_id, balance, created_at, last_activity) VALUES (?, ?, ?, ?)", (user_id, new_balance, current_time, current_time))
    
    conn.commit()
    conn.close()
    logger.info(f"User {user_id} wallet updated. New balance: {new_balance}")
    return new_balance

async def update_user_activity_db(user_id: int):
    """تحديث آخر نشاط للمستخدم."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    current_time = datetime.now().isoformat()
    cursor.execute("UPDATE users SET last_activity = ? WHERE user_id = ?", (current_time, user_id))
    conn.commit()
    conn.close()

# --- دوال المدفوعات المعلقة ---

async def add_pending_payment_db(user_id: int, username: str, amount: float, transaction_id: str, payment_method: str = "Unknown"):
    """إضافة طلب دفع معلق."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    payment_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO pending_payments (payment_id, user_id, username, amount, transaction_id, payment_method, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (payment_id, user_id, username, amount, transaction_id, payment_method, "pending", timestamp))
    
    conn.commit()
    conn.close()
    logger.info(f"Pending payment added for user {user_id}: {payment_id}")
    return payment_id

# --- دوال سجل المشتريات ---

async def add_purchase_history_db(user_id: int, username: str, product_name: str, game_id: str, price: float):
    """إضافة عملية شراء إلى السجل."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    purchase_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO purchases_history (purchase_id, user_id, username, product_name, game_id, price, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (purchase_id, user_id, username, product_name, game_id, price, "pending_shipment", timestamp))

    conn.commit()
    conn.close()
    logger.info(f"Purchase added for user {user_id}: {purchase_id}")
    return purchase_id

async def get_user_purchases_history_db(user_id: int):
    """جلب محتويات سلة المشتريات للمستخدم."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # جلب تفاصيل المنتج من جدول المنتجات
    cursor.execute("""
        SELECT 
            c.user_id, c.product_id, p.name, p.price, c.quantity, c.timestamp, p.icon
        FROM user_carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = ?
    """, (user_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    cart_items = []
    keys = ["user_id", "product_id", "product_name", "price", "quantity", "timestamp", "icon"]
    for row in results:
        cart_items.append(dict(zip(keys, row)))
    return cart_items

async def get_user_purchases_history_db(user_id: int):
    """جلب سجل مشتريات المستخدم."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM purchases_history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    results = cursor.fetchall()
    conn.close()
    
    history = []
    keys = ["purchase_id", "user_id", "username", "product_name", "game_id", "price", "status", "timestamp", "shipped_at"]
    for row in results:
        history.append(dict(zip(keys, row)))
    return history

async def get_purchase_by_details_db(user_id: int, product_name: str, status: str = 'pending_shipment'):
    """جلب عملية شراء محددة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT purchase_id FROM purchases_history
        WHERE user_id = ? AND product_name = ? AND status = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (user_id, product_name, status))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

async def update_purchase_status_db(purchase_id: str, status: str, shipped_at: str = None):
    """تحديث حالة عملية شراء."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    if shipped_at:
        cursor.execute("UPDATE purchases_history SET status = ?, shipped_at = ? WHERE purchase_id = ?", (status, shipped_at, purchase_id))
    else:
        cursor.execute("UPDATE purchases_history SET status = ? WHERE purchase_id = ?", (status, purchase_id))
    conn.commit()
    conn.close()
    logger.info(f"Purchase {purchase_id} status updated to {status}.")

# --- دوال الإحصائيات ---

async def get_total_users_db() -> int:
    """عدد المستخدمين الكلي."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(user_id) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    return total_users

async def get_new_users_today_db() -> int:
    """عدد المستخدمين الجدد اليوم."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    cursor.execute("SELECT COUNT(user_id) FROM users WHERE created_at >= ?", (today_start,))
    new_users = cursor.fetchone()[0]
    conn.close()
    return new_users

async def get_active_users_last_24_hours_db() -> int:
    """عدد المستخدمين النشطين في آخر 24 ساعة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    time_24_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
    cursor.execute("SELECT COUNT(user_id) FROM users WHERE last_activity >= ?", (time_24_hours_ago,))
    active_users = cursor.fetchone()[0]
    conn.close()
    return active_users

async def get_all_user_ids_db() -> list:
    """جلب جميع معرفات المستخدمين."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return user_ids

async def get_purchase_by_id_db(purchase_id: str):
    """جلب تفاصيل عملية شراء بواسطة المعرف."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM purchases_history WHERE purchase_id = ?", (purchase_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        keys = ["purchase_id", "user_id", "username", "product_name", "game_id", "price", "status", "timestamp", "shipped_at"]
        return dict(zip(keys, row))
    return None

# --- دوال الكوبونات ---

async def add_coupon_db(code: str, discount_type: str, discount_value: float, max_uses: int = 1):
    """إضافة كوبون جديد. discount_type: 'percent' أو 'fixed'"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO coupons (code, discount_type, discount_value, max_uses) VALUES (?, ?, ?, ?)",
            (code.upper(), discount_type, discount_value, max_uses)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

async def get_coupon_db(code: str):
    """جلب كوبون بالكود."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code.upper(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        keys = ["id", "code", "discount_type", "discount_value", "max_uses", "used_count", "is_active", "created_at"]
        return dict(zip(keys, row))
    return None

async def use_coupon_db(code: str):
    """تسجيل استخدام كوبون وتعطيله إن استنفد."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE coupons SET used_count = used_count + 1 WHERE code = ?", (code.upper(),))
    cursor.execute("UPDATE coupons SET is_active = 0 WHERE code = ? AND used_count >= max_uses", (code.upper(),))
    conn.commit()
    conn.close()

async def get_all_coupons_db():
    """جلب جميع الكوبونات."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coupons ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    keys = ["id", "code", "discount_type", "discount_value", "max_uses", "used_count", "is_active", "created_at"]
    return [dict(zip(keys, r)) for r in rows]

async def delete_coupon_db(code: str):
    """حذف كوبون."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM coupons WHERE code = ?", (code.upper(),))
    conn.commit()
    conn.close()


# --- دوال إحصائيات متقدمة ---

async def get_total_revenue_db() -> float:
    """إجمالي الإيرادات من المشتريات المكتملة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(price), 0) FROM purchases_history WHERE status IN ('Shipped','shipped','completed')")
    result = cursor.fetchone()[0]
    conn.close()
    return float(result)

async def get_total_orders_db() -> int:
    """إجمالي عدد الطلبات."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM purchases_history")
    result = cursor.fetchone()[0]
    conn.close()
    return result

async def get_pending_orders_db():
    """جلب الطلبات المعلقة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM purchases_history WHERE status IN ('pending_shipment','pending') ORDER BY timestamp DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    keys = ["purchase_id","user_id","username","product_name","game_id","price","status","timestamp","shipped_at"]
    return [dict(zip(keys, r)) for r in rows]

async def get_pending_deposits_db():
    """جلب طلبات الإيداع المعلقة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pending_payments WHERE status = 'pending' ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    keys = ["payment_id","user_id","username","amount","transaction_id","payment_method","status","timestamp"]
    return [dict(zip(keys, r)) for r in rows]

async def get_top_products_db(limit: int = 5):
    """أكثر المنتجات مبيعاً."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT product_name, COUNT(*) as cnt, SUM(price) as revenue FROM purchases_history GROUP BY product_name ORDER BY cnt DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"product_name": r[0], "count": r[1], "revenue": r[2]} for r in rows]

async def get_user_info_db(user_id: int):
    """جلب معلومات مستخدم."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        keys = ["user_id","username","balance","created_at","last_activity"]
        return dict(zip(keys, row))
    return None

async def set_user_balance_db(user_id: int, new_balance: float):
    """تعيين رصيد مستخدم مباشرة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()

async def get_revenue_today_db() -> float:
    """إيرادات اليوم."""
    from datetime import date
    today = str(date.today())
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COALESCE(SUM(price), 0) FROM purchases_history WHERE status IN ('Shipped','shipped','completed') AND timestamp LIKE ?",
        (today + '%',)
    )
    result = cursor.fetchone()[0]
    conn.close()
    return float(result)

# --- دوال العملات ---

async def get_exchange_rate_db() -> float:
    """جلب سعر صرف الدولار إلى الليرة السورية."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'usd_to_syp'")
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row else 12000.0

async def set_exchange_rate_db(rate: float):
    """تحديث سعر الصرف."""
    from datetime import datetime
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('usd_to_syp', ?, ?)",
        (str(rate), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()

async def get_user_currency_db(user_id: int) -> str:
    """جلب عملة المستخدم المفضّلة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT currency FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return row[0]
    return 'USD'

async def set_user_currency_db(user_id: int, currency: str):
    """تعيين عملة المستخدم."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # تأكد من وجود المستخدم أولاً
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, currency) VALUES (?, ?)",
        (user_id, currency)
    )
    cursor.execute(
        "UPDATE users SET currency = ? WHERE user_id = ?",
        (currency, user_id)
    )
    conn.commit()
    conn.close()

# --- دوال الإحالة ---

async def init_referral_tables():
    """إنشاء جداول الإحالة والعروض إن لم تكن موجودة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL UNIQUE,
            reward_paid INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flash_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            discounted_price REAL NOT NULL,
            original_price REAL NOT NULL,
            expires_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO settings (key, value) VALUES ('referral_reward', '0.50')
    """)
    conn.commit()
    conn.close()

async def add_referral_db(referrer_id: int, referred_id: int) -> bool:
    """تسجيل إحالة جديدة. يعيد True إذا نجح."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
            (referrer_id, referred_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

async def get_referral_stats_db(user_id: int) -> dict:
    """إحصائيات الإحالة لمستخدم."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,))
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND reward_paid = 1", (user_id,))
    paid = cursor.fetchone()[0]
    conn.close()
    return {"total": total, "paid": paid}

async def mark_referral_rewarded_db(referred_id: int):
    """تحديد الإحالة كمدفوعة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE referrals SET reward_paid = 1 WHERE referred_id = ?",
        (referred_id,)
    )
    conn.commit()
    conn.close()

async def get_referrer_db(referred_id: int):
    """جلب المُحيل لمستخدم معين."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT referrer_id FROM referrals WHERE referred_id = ? AND reward_paid = 0",
        (referred_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

async def get_referral_reward_db() -> float:
    """جلب قيمة مكافأة الإحالة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'referral_reward'")
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row else 0.5

async def set_referral_reward_db(amount: float):
    """تحديث قيمة مكافأة الإحالة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('referral_reward', ?)",
        (str(amount),)
    )
    conn.commit()
    conn.close()

# --- دوال العروض المحدودة ---

async def add_flash_offer_db(product_id: str, discounted_price: float, original_price: float, expires_at: str) -> int:
    """إضافة عرض محدود الوقت."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO flash_offers (product_id, discounted_price, original_price, expires_at) VALUES (?, ?, ?, ?)",
        (product_id, discounted_price, original_price, expires_at)
    )
    offer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return offer_id

async def get_active_flash_offers_db() -> list:
    """جلب العروض النشطة وغير المنتهية."""
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM flash_offers WHERE is_active = 1 AND expires_at > ? ORDER BY expires_at ASC",
        (now,)
    )
    rows = cursor.fetchall()
    conn.close()
    keys = ["id","product_id","discounted_price","original_price","expires_at","is_active","created_at"]
    return [dict(zip(keys, r)) for r in rows]

async def get_flash_offer_by_product_db(product_id: str) -> dict:
    """جلب عرض نشط لمنتج معين."""
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM flash_offers WHERE product_id = ? AND is_active = 1 AND expires_at > ? LIMIT 1",
        (product_id, now)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        keys = ["id","product_id","discounted_price","original_price","expires_at","is_active","created_at"]
        return dict(zip(keys, row))
    return None

async def deactivate_flash_offer_db(offer_id: int):
    """إلغاء عرض."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE flash_offers SET is_active = 0 WHERE id = ?", (offer_id,))
    conn.commit()
    conn.close()

# --- دوال دعم العملاء ---

async def init_support_table():
    """إنشاء جدول التذاكر."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            subject TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES support_tickets(id)
        )
    """)
    conn.commit()
    conn.close()

async def create_ticket_db(user_id: int, username: str, subject: str) -> int:
    """إنشاء تذكرة جديدة، يعيد ticket_id."""
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO support_tickets (user_id, username, subject, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, username, subject, now, now)
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

async def add_ticket_message_db(ticket_id: int, sender: str, message: str):
    """إضافة رسالة لتذكرة."""
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO support_messages (ticket_id, sender, message, sent_at) VALUES (?, ?, ?, ?)",
        (ticket_id, sender, message, now)
    )
    cursor.execute(
        "UPDATE support_tickets SET updated_at = ?, status = CASE WHEN status = 'closed' THEN 'open' ELSE status END WHERE id = ?",
        (now, ticket_id)
    )
    conn.commit()
    conn.close()

async def get_user_tickets_db(user_id: int) -> list:
    """جلب تذاكر مستخدم."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM support_tickets WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    keys = ["id", "user_id", "username", "subject", "status", "created_at", "updated_at"]
    return [dict(zip(keys, r)) for r in rows]

async def get_ticket_messages_db(ticket_id: int) -> list:
    """جلب رسائل تذكرة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM support_messages WHERE ticket_id = ? ORDER BY sent_at ASC",
        (ticket_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    keys = ["id", "ticket_id", "sender", "message", "sent_at"]
    return [dict(zip(keys, r)) for r in rows]

async def get_ticket_by_id_db(ticket_id: int) -> dict:
    """جلب تذكرة بالـ ID."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        keys = ["id", "user_id", "username", "subject", "status", "created_at", "updated_at"]
        return dict(zip(keys, row))
    return None

async def get_open_tickets_db() -> list:
    """جلب جميع التذاكر المفتوحة للأدمن."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM support_tickets WHERE status != 'closed' ORDER BY updated_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    keys = ["id", "user_id", "username", "subject", "status", "created_at", "updated_at"]
    return [dict(zip(keys, r)) for r in rows]

async def close_ticket_db(ticket_id: int):
    """إغلاق تذكرة."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE support_tickets SET status = 'closed' WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()

# --- دوال الاسترداد ---

async def request_refund_db(purchase_id: str, user_id: int, reason: str) -> bool:
    """طلب استرداد."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refund_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "INSERT INTO refund_requests (purchase_id, user_id, reason) VALUES (?, ?, ?)",
            (purchase_id, user_id, reason)
        )
        cursor.execute(
            "UPDATE purchases_history SET status = 'refund_requested' WHERE purchase_id = ? AND user_id = ?",
            (purchase_id, user_id)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

async def get_pending_refunds_db() -> list:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refund_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "SELECT r.*, p.product_name, p.price, p.username FROM refund_requests r "
            "JOIN purchases_history p ON r.purchase_id = p.purchase_id "
            "WHERE r.status = 'pending' ORDER BY r.created_at DESC"
        )
        rows = cursor.fetchall()
        keys = ["id","purchase_id","user_id","reason","status","created_at","product_name","price","username"]
        return [dict(zip(keys, r)) for r in rows]
    finally:
        conn.close()

async def process_refund_db(purchase_id: str, approve: bool) -> dict:
    """معالجة طلب الاسترداد. يعيد بيانات المستخدم والمبلغ."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM purchases_history WHERE purchase_id = ?", (purchase_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {}
    keys = ["purchase_id","user_id","username","product_name","game_id","price","status","timestamp","shipped_at"]
    purchase = dict(zip(keys, row))
    if approve:
        cursor.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (purchase['price'], purchase['user_id'])
        )
        cursor.execute(
            "UPDATE purchases_history SET status = 'refunded' WHERE purchase_id = ?",
            (purchase_id,)
        )
        cursor.execute(
            "UPDATE refund_requests SET status = 'approved' WHERE purchase_id = ?",
            (purchase_id,)
        )
    else:
        cursor.execute(
            "UPDATE purchases_history SET status = 'Shipped' WHERE purchase_id = ?",
            (purchase_id,)
        )
        cursor.execute(
            "UPDATE refund_requests SET status = 'rejected' WHERE purchase_id = ?",
            (purchase_id,)
        )
    conn.commit()
    conn.close()
    return purchase

# --- دوال اللغة ---

async def get_user_language_db(user_id: int) -> str:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ar'")
        conn.commit()
    except Exception:
        pass
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return (row[0] or 'ar') if row else 'ar'

async def set_user_language_db(user_id: int, lang: str):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, language) VALUES (?, ?)", (user_id, lang))
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

# --- دوال التحقق بخطوتين ---

async def set_user_2fa_db(user_id: int, enabled: bool):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN two_fa INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    cursor.execute("UPDATE users SET two_fa = ? WHERE user_id = ?", (1 if enabled else 0, user_id))
    conn.commit()
    conn.close()

async def get_user_2fa_db(user_id: int) -> bool:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN two_fa INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    cursor.execute("SELECT two_fa FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row else False
