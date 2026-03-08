# keyboards.py - مع دعم تعدد اللغات
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

MENU_BUTTONS = {
    'ar': [
        [KeyboardButton("🎮 الألعاب"), KeyboardButton("📱 أرقام التفعيلات")],
        [KeyboardButton("⚡ العروض"), KeyboardButton("💰 محفظتي")],
        [KeyboardButton("📋 طلباتي"), KeyboardButton("🔗 إحالة صديق")],
        [KeyboardButton("⚙️ إعداداتي"), KeyboardButton("💬 دعم العملاء")],
        [KeyboardButton("ℹ️ معلومات عنا")],
        [KeyboardButton("🏠 القائمة الرئيسية")],
    ],
    'en': [
        [KeyboardButton("🎮 Games"), KeyboardButton("📱 Activations")],
        [KeyboardButton("⚡ Offers"), KeyboardButton("💰 My Wallet")],
        [KeyboardButton("📋 My Orders"), KeyboardButton("🔗 Refer a Friend")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("💬 Support")],
        [KeyboardButton("ℹ️ About Us")],
        [KeyboardButton("🏠 Main Menu")],
    ],
    'ku': [
        [KeyboardButton("🎮 یاریەکان"), KeyboardButton("📱 چالاككردن")],
        [KeyboardButton("⚡ پێشکەشکردنەکان"), KeyboardButton("💰 جزدانەکەم")],
        [KeyboardButton("📋 داواکارییەکانم"), KeyboardButton("🔗 هاوڕێ بانەوە")],
        [KeyboardButton("⚙️ ڕێکخستنەکان"), KeyboardButton("💬 پشتگیری")],
        [KeyboardButton("ℹ️ دەربارە")],
        [KeyboardButton("🏠 پێڕستی سەرەکی")],
    ],
}

# جميع نصوص الأزرار لكل اللغات (للمعالجة في handle_message)
ALL_BUTTON_TEXTS = {
    'games':    ["🎮 الألعاب", "🎮 Games", "🎮 یاریەکان"],
    'activate': ["📱 أرقام التفعيلات", "📱 Activations", "📱 چالاككردن"],
    'offers':   ["⚡ العروض", "⚡ Offers", "⚡ پێشکەشکردنەکان"],
    'wallet':   ["💰 محفظتي", "💰 My Wallet", "💰 جزدانەکەم"],
    'orders':   ["📋 طلباتي", "📋 My Orders", "📋 داواکارییەکانم"],
    'referral': ["🔗 إحالة صديق", "🔗 Refer a Friend", "🔗 هاوڕێ بانەوە"],
    'settings': ["⚙️ إعداداتي", "⚙️ Settings", "⚙️ ڕێکخستنەکان"],
    'support':  ["💬 دعم العملاء", "💬 Support", "💬 پشتگیری"],
    'about':    ["ℹ️ معلومات عنا", "ℹ️ About Us", "ℹ️ دەربارە"],
    'home':     ["🏠 القائمة الرئيسية", "🏠 Main Menu", "🏠 پێڕستی سەرەکی"],
}

def get_main_menu_keyboard(lang: str = 'ar') -> ReplyKeyboardMarkup:
    keyboard = MENU_BUTTONS.get(lang, MENU_BUTTONS['ar'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_back_to_main_keyboard(lang: str = 'ar') -> ReplyKeyboardMarkup:
    home_text = ALL_BUTTON_TEXTS['home'][['ar','en','ku'].index(lang) if lang in ['ar','en','ku'] else 0]
    keyboard = [[KeyboardButton(home_text)]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def detect_button(text: str) -> str:
    """يكتشف أي زر ضغط المستخدم بغض النظر عن اللغة."""
    for action, texts in ALL_BUTTON_TEXTS.items():
        if text in texts:
            return action
    return 'unknown'

def get_wallet_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("سيرياتيل كاش 📞", callback_data="deposit_syriatel_cash")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(buttons)
