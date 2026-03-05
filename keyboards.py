# keyboards.py - النسخة المحسنة
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from database import get_all_categories_db, get_subcategories_by_category_db, get_servers_by_subcategory_db, get_products_by_parent_db, get_product_by_id_db

# ملاحظة: تم إزالة الاستيراد من 'data' واستبداله بالاستيراد من 'database'

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🎮 الألعاب"), KeyboardButton("📱 أرقام التفعيلات")],
        [KeyboardButton("🛒 سلة المشتريات"), KeyboardButton("💰 محفظتي")],
        [KeyboardButton("📋 طلباتي"), KeyboardButton("📞 التواصل معنا")],
        [KeyboardButton("ℹ️ معلومات عنا"), KeyboardButton("🏠 القائمة الرئيسية")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_back_to_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton("🏠 القائمة الرئيسية")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# تم إزالة الدوال التي تعتمد على 'data.py' من هنا
# وسيتم بناء لوحات المفاتيح الخاصة بالمنتجات مباشرة في bot.py باستخدام دوال قاعدة البيانات
# لضمان أن تكون لوحات المفاتيح ديناميكية وتعتمد على البيانات المخزنة في قاعدة البيانات.

# تم الإبقاء على الدوال الأساسية فقط التي لا تعتمد على هيكل المنتجات القديم.
# الدوال الخاصة بالمنتجات (get_categories_keyboard, get_subcategories_keyboard, إلخ)
# تم نقل منطقها إلى bot.py لتعمل مع قاعدة البيانات الجديدة.

def get_wallet_keyboard() -> InlineKeyboardMarkup:
    # هذه الدالة ستعتمد على PAYMENT_METHODS في config.py، لكن سنبقيها بسيطة هنا
    # لأن المنطق المعقد تم نقله إلى دالة wallet في bot.py
    buttons = [
        [InlineKeyboardButton("سيرياتيل كاش 📞", callback_data="deposit_syriatel_cash")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(buttons)
