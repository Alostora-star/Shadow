# bot.py - النسخة المحسنة
import os
import logging
import uuid
import html
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from telegram.helpers import escape_markdown
from telegram.error import BadRequest

def escape_html(text: str | None) -> str:
    """Helper function to escape HTML characters safely."""
    if text is None:
        return ""
    # تحويل النص إلى سلسلة نصية وتنظيفه من أي علامات HTML قد تسبب مشاكل
    safe_text = html.escape(str(text))
    return safe_text

# --- دوال مساعدة ---

async def edit_or_reply_message(update: Update, message: str, keyboard: list = None) -> None:
    """تعديل الرسالة الحالية إذا كانت callback_query، وإلا إرسال رسالة جديدة."""
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message, 
                reply_markup=reply_markup, 
                parse_mode=ParseMode.HTML
            )
        except BadRequest:
            # إذا فشل التعديل (مثلاً، إذا كانت الرسالة قديمة جداً)، نرسل رسالة جديدة
            await update.callback_query.message.reply_text(
                message, 
                reply_markup=reply_markup, 
                parse_mode=ParseMode.HTML
            )
        await update.callback_query.answer()
    elif update.message:
        await update.message.reply_text(
            message, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.HTML
        )

# --- دوال التحقق من القناة ---
from telegram.constants import ParseMode

from config import (
    BOT_TOKEN, WEBSITE_NAME, WEBSITE_SLOGAN, WEBSITE_DESCRIPTION, 
    WEBSITE_MESSAGE, INSTAGRAM_USERNAME, ADMIN_USER_ID, GROUP_ID, 
    GROUP_JOIN_LINK, PAYMENT_METHODS
)

from database import (
    get_product_by_id_db,
    init_db, get_user_wallet_db, update_user_wallet_db, add_pending_payment_db,
    add_purchase_history_db, get_user_purchases_history_db, update_purchase_status_db,
    get_purchase_by_details_db, get_total_users_db, get_new_users_today_db,
    get_purchase_by_id_db,
    get_active_users_last_24_hours_db, update_user_activity_db, get_all_user_ids_db,
    add_to_cart_db, get_user_cart_db, clear_user_cart_db, remove_from_cart_db,
    get_all_categories_db, get_subcategories_by_category_db, get_servers_by_subcategory_db,
    get_products_by_parent_db, get_product_by_id_db,
    save_game_id_db, get_saved_game_ids_db, delete_saved_game_id_db
)

from keyboards import get_main_menu_keyboard, get_back_to_main_keyboard

# استيراد معالجات المسؤول
from admin_handlers import (
    admin_panel, admin_add_category_start, admin_add_category_name, admin_add_category_desc,
    admin_list_categories, admin_add_product_start, admin_add_product_name, admin_add_product_price,
    admin_add_product_desc, admin_add_product_category, admin_add_product_subcategory,
    admin_add_product_server, admin_list_products, admin_edit_product_start, admin_edit_product_price,
    admin_delete_product_start, admin_delete_product, cancel_admin_operation,
    ADD_CATEGORY_NAME, ADD_CATEGORY_DESC, ADD_PRODUCT_NAME, ADD_PRODUCT_PRICE,
    ADD_PRODUCT_DESC, ADD_PRODUCT_CATEGORY, ADD_PRODUCT_SUBCATEGORY, ADD_PRODUCT_SERVER,
    EDIT_PRODUCT_PRICE
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- حالات المحادثة ---
SYRIATEL_CASH_AMOUNT, SYRIATEL_CASH_TRANSACTION_ID = range(2)
SYRIATEL_CODE_AMOUNT, SYRIATEL_CODE_TRANSACTION_ID = range(10, 12)
SHAM_CASH_AMOUNT, SHAM_CASH_PHOTO = range(20, 22)
ASK_GAME_ID, CHOOSE_SAVED_GAME_ID, SAVE_NEW_GAME_ID = range(3, 6)
BROADCAST_MESSAGE = 7
GAME_ID_INPUT = 8

# --- دوال مساعدة ---



async def get_user_wallet(user_id: int) -> float:
    """جلب رصيد المحفظة."""
    return await get_user_wallet_db(user_id)

async def update_user_wallet(user_id: int, amount: float, username: str = None):
    """تحديث رصيد المحفظة."""
    await update_user_wallet_db(user_id, amount, username)

async def add_pending_payment(user_id: int, username: str, amount: float, transaction_id: str, payment_method: str = "Unknown", context: ContextTypes.DEFAULT_TYPE = None):
    """إضافة طلب دفع معلق."""
    # ضمان تحويل البيانات لأنواع بسيطة لمنع أخطاء SQLite
    payment_id = await add_pending_payment_db(
        int(user_id), 
        str(username), 
        float(amount), 
        str(transaction_id), 
        str(payment_method)
    )
    
    logger.info(f"Pending payment added for user {user_id}: {payment_id} via {payment_method}")

    if context and ADMIN_USER_ID:
        # إرسال رسالة نصية مجردة تماماً للأدمن لضمان الوصول 100%
        admin_notification_message = (
            f"🔔 طلب إيداع جديد!\n\n"
            f"المستخدم: {username} (ID: {user_id})\n"
            f"المبلغ: ${amount:.2f}\n"
            f"رقم العملية: {transaction_id}\n"
            f"الطريقة: {payment_method}\n"
            f"✅ للتأكيد (اضغط للنسخ):\n<code>/admin_confirm_deposit {user_id} {amount:.2f}</code>"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text=admin_notification_message)
            logger.info(f"Admin {ADMIN_USER_ID} notified about new pending payment {payment_id}.")
        except Exception as e:
            logger.error(f"Critical: Failed to send admin notification: {str(e)}")

    return payment_id

async def send_channel_join_message(update: Update, user_id: int, first_name: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة الانضمام للقناة."""
    if GROUP_ID and GROUP_JOIN_LINK: 
        await context.bot.send_message(
            chat_id=user_id,
            text=f"مرحباً {first_name}!\n\n"
                 f"لاستخدام البوت والاستفادة من خدماتنا، يرجى الانضمام إلى قناتنا على تليجرام.\n"
                 f"الرجاء الانضمام من خلال هذا الرابط: {GROUP_JOIN_LINK}\n\n"
                 f"بعد الانضمام، يمكنك الاستمرار في استخدام البوت."
        )
        context.user_data['channel_join_message_sent'] = True 
    else:
        logger.error("GROUP_ID or GROUP_JOIN_LINK is not set in config.py.")

# --- دوال العرض ---

async def show_about_us(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض معلومات عن المتجر."""
    about_message = f"""
ℹ️ معلومات عن {WEBSITE_NAME}

🎯 رؤيتنا:
{WEBSITE_DESCRIPTION}

⭐ قيمنا:
{WEBSITE_SLOGAN}

📝 رسالتنا:
{WEBSITE_MESSAGE}

🔹 نحن متخصصون في توفير جميع أنواع الخدمات الرقمية
🔹 أسعار تنافسية وجودة عالية
🔹 خدمة عملاء متميزة على مدار الساعة
🔹 تسليم فوري للطلبات

تابعنا على انستغرام: {INSTAGRAM_USERNAME}
    """
    if update.message: 
        await update.message.reply_text(about_message, reply_markup=get_back_to_main_keyboard())
    elif update.callback_query: 
        await update.callback_query.message.reply_text(about_message, reply_markup=get_back_to_main_keyboard())
        try:
            await update.callback_query.delete_message()
        except BadRequest:
            pass

async def show_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض معلومات التواصل."""
    contact_message = f"""
📞 معلومات التواصل

🔹 للاستفسارات والدعم الفني:
📧 البريد الإلكتروني: support@example.com
📱 انستغرام: {INSTAGRAM_USERNAME}

🔹 أوقات العمل:
🕐 24/7 خدمة متواصلة

🔹 طرق الدفع المتاحة:
💰 محافظ إلكترونية
    """
    if update.message:
        await update.message.reply_text(contact_message, reply_markup=get_back_to_main_keyboard())
    elif update.callback_query:
        await update.callback_query.message.reply_text(contact_message, reply_markup=get_back_to_main_keyboard())
        try:
            await update.callback_query.delete_message()
        except BadRequest:
            pass

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض سلة المشتريات."""
    user_id = update.effective_user.id
    cart = await get_user_cart_db(user_id)
    
    keyboard_buttons = []
    message = ""
    
    if not cart:
        message = "🛒 سلة المشتريات فارغة\n\nابدأ بتصفح المنتجات وإضافة ما تريد!"
    else:
        message = "🛒 سلة المشتريات:\n\n"
        total = 0
        for item in cart:
            item_name = item['product_name']
            price = item['price']
            product_id = item['product_id']
            total += price
            message += f"• {item_name}\n💰 السعر: ${price:.2f}\n"
            keyboard_buttons.append([InlineKeyboardButton(f"💳 شراء الآن: {item_name}", callback_data=f"buy_cart_item_{product_id}")])
            message += "\n"

        message += f"💵 المجموع الكلي: ${total:.2f}\n\n"

    keyboard_buttons.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")])

    if update.message:
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard_buttons))
    elif update.callback_query:
        await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard_buttons))
        try:
            await update.callback_query.delete_message()
        except BadRequest:
            pass

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض الطلبات السابقة."""
    user_id = update.effective_user.id
    orders = await get_user_purchases_history_db(user_id)
    
    if not orders:
        message = "📋 طلباتي\n\nلا توجد طلبات سابقة حتى الآن.\n\nعند إتمام أول عملية شراء، ستظهر طلباتك هنا."
    else:
        message = "📋 طلباتي السابقة:\n\n"
        for i, order in enumerate(orders):
            message += (
                f"<b>الطلب رقم {i+1}:</b>\n"
                f"  المنتج: {escape_html(order.get('product_name', 'N/A'))}\n"
                f"  المبلغ: ${order.get('price', 0.0):.2f}\n"
                f"  معرف اللعبة: <code>{escape_html(order.get('game_id', 'N/A'))}</code>\n"
                f"  الحالة: {escape_html(order.get('status', 'N/A'))}\n"
                f"  التاريخ: {escape_html(order.get('timestamp', 'N/A'))}\n\n"
            )
    
    if update.message:
        await update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=get_back_to_main_keyboard())
    elif update.callback_query:
        await update.callback_query.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=get_back_to_main_keyboard())
        try:
            await update.callback_query.delete_message()
        except BadRequest:
            pass

# --- دوال الألعاب ---

async def show_games(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض قائمة الألعاب المتاحة."""
    message = "🎮 مرحباً بك في قسم الألعاب!\n\nاختر اللعبة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("🔥 فري فاير (Free Fire)", callback_data="game_freefire")],
        [InlineKeyboardButton("🎯 ببجي (PUBG)", callback_data="game_pubg")],
        [InlineKeyboardButton("♣️ JAWAKER", callback_data="game_jawaker")],
        [InlineKeyboardButton("🪙 FC Mobile", callback_data="game_fcmobile")],
        [InlineKeyboardButton("🔫 Call of Duty", callback_data="game_cod")],
        [InlineKeyboardButton("🌊 Wild Rift", callback_data="game_wildrift")],
        [InlineKeyboardButton("🏰 Age Of Empires", callback_data="game_aoe")],
        [InlineKeyboardButton("🤴 Honor of Kings", callback_data="game_hok")],
        [InlineKeyboardButton("🛡️ Lords Mobile", callback_data="game_lordsmobile")],
        [InlineKeyboardButton("✨ GENSHIN IMPACT", callback_data="game_genshin")],
        [InlineKeyboardButton("😁 Mobile Legends", callback_data="game_mobilelegends")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")]
    ]
    
    if update.message:
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest:
            await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def show_activations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض قائمة أرقام التفعيلات."""
    message = "📱 مرحباً بك في قسم أرقام التفعيلات!\n\nاختر الخدمة التي تريد تفعيلها:"
    
    keyboard = [
        [InlineKeyboardButton("🔹 تفعيل تليجرام (Telegram)", callback_data="act_telegram")],
        [InlineKeyboardButton("🔹 تفعيل واتساب (WhatsApp)", callback_data="act_whatsapp")],
        [InlineKeyboardButton("🔹 تفعيل Apple ID", callback_data="act_apple")],
        [InlineKeyboardButton("🔹 تفعيل حساب Google", callback_data="act_google")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")]
    ]
    
    if update.message:
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest:
            await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def show_freefire_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات فري فاير."""
    message = (
        "🔥 <b>فري فاير (Free Fire)</b>\n\n"
        "اختر الباقة التي تريدها:"
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 100 الماسة - $1.00", callback_data="buy_freefire_100")],
        [InlineKeyboardButton("💎 210 الماسة - $2.00", callback_data="buy_freefire_210")],
        [InlineKeyboardButton("💎 520 الماسة - $5.00", callback_data="buy_freefire_520")],
        [InlineKeyboardButton("💎 1080 الماسة - $10.00", callback_data="buy_freefire_1080")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest:
            await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def show_pubg_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات ببجي."""
    message = "🎯 <b>ببجي</b>\n\nاختر الباقة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("💸 60 UC - $0.95", callback_data="buy_pubg_60")],
        [InlineKeyboardButton("💸 120 UC - $1.90", callback_data="buy_pubg_120")],
        [InlineKeyboardButton("💸 325 UC - $4.70", callback_data="buy_pubg_325")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)

async def show_jawaker_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات جواكر."""
    message = "♣️ <b>جواكر</b>\n\nاختر الباقة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("10000 ♣️ - $1.5", callback_data="buy_jawaker_10000")],
        [InlineKeyboardButton("مسرع الاحمر ♦️ - $2", callback_data="buy_jawaker_red")],
        [InlineKeyboardButton("مسرع اسود ♣️ - $17", callback_data="buy_jawaker_black")],
        [InlineKeyboardButton("مسرع ازرق 🏄‍♂️ - $9", callback_data="buy_jawaker_blue")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)

async def show_fcmobile_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات FC Mobile."""
    message = "🪙 <b>FC Mobile</b>\n\nاختر الباقة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("99 🥈 - $1.5", callback_data="buy_fcmobile_99s")],
        [InlineKeyboardButton("499 🥈 - $7.5", callback_data="buy_fcmobile_499s")],
        [InlineKeyboardButton("999 🥈 - $14", callback_data="buy_fcmobile_999s")],
        [InlineKeyboardButton("100 point 🪙 - $1.5", callback_data="buy_fcmobile_100p")],
        [InlineKeyboardButton("500 point 🪙 - $7.5", callback_data="buy_fcmobile_500p")],
        [InlineKeyboardButton("1070 point 🪙 - $14", callback_data="buy_fcmobile_1070p")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)

async def show_cod_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات Call of Duty."""
    message = "🔫 <b>Call of Duty</b>\n\nاختر الباقة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("88 🪙 - $1.5", callback_data="buy_cod_88")],
        [InlineKeyboardButton("460 🪙 - $7", callback_data="buy_cod_460")],
        [InlineKeyboardButton("Battle Pass 💎💫 - $3.5", callback_data="buy_cod_bp")],
        [InlineKeyboardButton("Battle Pass Blunde 💪 - $8", callback_data="buy_cod_bpb")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)

async def show_wildrift_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات Wild Rift."""
    message = "🌊 <b>Wild Rift</b>\n\nاختر الباقة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("425 🪙 - $6", callback_data="buy_wildrift_425")],
        [InlineKeyboardButton("STELLA CORN - $6.5", callback_data="buy_wildrift_stella")],
        [InlineKeyboardButton("1000 🪙 - $14", callback_data="buy_wildrift_1000")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)

async def show_aoe_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات Age Of Empires."""
    message = "🏰 <b>Age Of Empires</b>\n\nاختر الباقة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("99 🪙 - $1.3", callback_data="buy_aoe_99")],
        [InlineKeyboardButton("499 🪙 - $6.5", callback_data="buy_aoe_499")],
        [InlineKeyboardButton("999 🪙 - $12.5", callback_data="buy_aoe_999")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)

async def show_hok_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات Honor of Kings."""
    message = "🤴 <b>Honor of Kings</b>\n\nاختر الباقة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("400 💸 - $6", callback_data="buy_hok_400")],
        [InlineKeyboardButton("800 💸 - $12", callback_data="buy_hok_800")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)

async def show_lordsmobile_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات Lords Mobile."""
    message = "🛡️ <b>Lords Mobile</b>\n\nاختر الباقة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("195 💎 - $2.5", callback_data="buy_lordsmobile_195")],
        [InlineKeyboardButton("395 💎 - $6.5", callback_data="buy_lordsmobile_395")],
        [InlineKeyboardButton("785 💎 - $11", callback_data="buy_lordsmobile_785")],
        [InlineKeyboardButton("أسبوعية 💎 - $2.5", callback_data="buy_lordsmobile_weekly")],
        [InlineKeyboardButton("شهرية 💎 - $27", callback_data="buy_lordsmobile_monthly")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)

async def show_genshin_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات Genshin Impact."""
    message = "✨ <b>GENSHIN IMPACT</b>\n\nاختر الباقة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("60 🔮 - $1", callback_data="buy_genshin_60")],
        [InlineKeyboardButton("330 🔮 - $5", callback_data="buy_genshin_330")],
        [InlineKeyboardButton("القمر ويكلين 🔮 - $5", callback_data="buy_genshin_moon")],
        [InlineKeyboardButton("1090 🔮 - $16", callback_data="buy_genshin_1090")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)

async def show_mobilelegends_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض باقات Mobile Legends."""
    message = "😁 <b>Mobile Legends</b>\n\nاختر الباقة التي تريد شحنها:"
    
    keyboard = [
        [InlineKeyboardButton("56 💎 - $1.4", callback_data="buy_mobilelegends_56")],
        [InlineKeyboardButton("86 💎 - $1.8", callback_data="buy_mobilelegends_86")],
        [InlineKeyboardButton("170 💎 - $3.5", callback_data="buy_mobilelegends_170")],
        [InlineKeyboardButton("255 💎 - $6", callback_data="buy_mobilelegends_255")],
        [InlineKeyboardButton("Weekly Diamond Pass 💎 - $2.6", callback_data="buy_mobilelegends_weeklypass")],
        [InlineKeyboardButton("Twilight Pass ✨ 💎 - $11", callback_data="buy_mobilelegends_twilight")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)


    """عرض باقات ببجي."""
    message = (
        "🎯 <b>ببجي (PUBG)</b>\n\n"
        "اختر الباقة التي تريدها:"
    )
    
    keyboard = [
        [InlineKeyboardButton("💸 60 UC - $0.95", callback_data="buy_pubg_60")],
        [InlineKeyboardButton("💸 120 UC - $1.90", callback_data="buy_pubg_120")],
        [InlineKeyboardButton("💸 325 UC - $4.70", callback_data="buy_pubg_325")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_games")]
    ]
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest:
            await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def show_freefire_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لفري فاير."""
    packages = {
        "100": {"diamonds": "100", "price": 1.00},
        "210": {"diamonds": "210", "price": 2.00},
        "520": {"diamonds": "520", "price": 5.00},
        "1080": {"diamonds": "1080", "price": 10.00}
    }
    
    if package not in packages:
        await update.callback_query.answer("❌ باقة غير صحيحة!")
        return
    
    pkg = packages[package]
    escaped_price = escape_html(f'${pkg["price"]:.2f}')
    message = (
        f"💎 <b>فري فاير - {escape_html(pkg['diamonds'])} الماسة</b>\n\n"
        f"💰 <b>السعر:</b> {escaped_price}\n\n"
        f"❓ <b>هل تريد شراء هذه الباقة\u061f</b>\n\n"
        f"✅ اضغط على 'نعم، شراء' للمتابعة\n"
        f"⚠️ سيتم خصم المبلغ من محفظتك"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ نعم، شراء", callback_data=f"confirm_freefire_{package}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_freefire")]
    ]
    
    try:
        await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest:
        await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def show_pubg_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لببجي."""
    packages = {
        "60": {"name": "ببجي - 60 UC", "price": 0.95},
        "120": {"name": "ببجي - 120 UC", "price": 1.90},
        "325": {"name": "ببجي - 325 UC", "price": 4.70}
    }
    await display_payment_page(update, context, "pubg", package, packages)

async def show_jawaker_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لجواكر."""
    packages = {
        "10000": {"name": "10000 ♣️", "price": 1.5},
        "red": {"name": "مسرع الاحمر ♦️", "price": 2.0},
        "black": {"name": "مسرع اسود ♣️", "price": 17.0},
        "blue": {"name": "مسرع ازرق 🏄‍♂️", "price": 9.0}
    }
    await display_payment_page(update, context, "jawaker", package, packages)

async def show_fcmobile_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لـ FC Mobile."""
    packages = {
        "99s": {"name": "99 🥈", "price": 1.5},
        "499s": {"name": "499 🥈", "price": 7.5},
        "999s": {"name": "999 🥈", "price": 14.0},
        "100p": {"name": "100 point 🪙", "price": 1.5},
        "500p": {"name": "500 point 🪙", "price": 7.5},
        "1070p": {"name": "1070 point 🪙", "price": 14.0}
    }
    await display_payment_page(update, context, "fcmobile", package, packages)

async def show_cod_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لـ Call of Duty."""
    packages = {
        "88": {"name": "88 🪙", "price": 1.5},
        "460": {"name": "460 🪙", "price": 7.0},
        "bp": {"name": "Battle Pass 💎💫", "price": 3.5},
        "bpb": {"name": "Battle Pass Blunde 💪", "price": 8.0}
    }
    await display_payment_page(update, context, "cod", package, packages)

async def show_wildrift_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لـ Wild Rift."""
    packages = {
        "425": {"name": "425 🪙", "price": 6.0},
        "stella": {"name": "STELLA CORN", "price": 6.5},
        "1000": {"name": "1000 🪙", "price": 14.0}
    }
    await display_payment_page(update, context, "wildrift", package, packages)

async def show_aoe_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لـ Age Of Empires."""
    packages = {
        "99": {"name": "99 🪙", "price": 1.3},
        "499": {"name": "499 🪙", "price": 6.5},
        "999": {"name": "999 🪙", "price": 12.5}
    }
    await display_payment_page(update, context, "aoe", package, packages)

async def show_hok_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لـ Honor of Kings."""
    packages = {
        "400": {"name": "400 💸", "price": 6.0},
        "800": {"name": "800 💸", "price": 12.0}
    }
    await display_payment_page(update, context, "hok", package, packages)

async def show_lordsmobile_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لـ Lords Mobile."""
    packages = {
        "195": {"name": "195 💎", "price": 2.5},
        "395": {"name": "395 💎", "price": 6.5},
        "785": {"name": "785 💎", "price": 11.0},
        "weekly": {"name": "أسبوعية 💎", "price": 2.5},
        "monthly": {"name": "شهرية 💎", "price": 27.0}
    }
    await display_payment_page(update, context, "lordsmobile", package, packages)

async def show_genshin_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لـ Genshin Impact."""
    packages = {
        "60": {"name": "60 🔮", "price": 1.0},
        "330": {"name": "330 🔮", "price": 5.0},
        "moon": {"name": "القمر ويكلين 🔮", "price": 5.0},
        "1090": {"name": "1090 🔮", "price": 16.0}
    }
    await display_payment_page(update, context, "genshin", package, packages)

async def show_mobilelegends_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str) -> None:
    """عرض صفحة الدفع لـ Mobile Legends."""
    packages = {
        "56": {"name": "56 💎", "price": 1.4},
        "86": {"name": "86 💎", "price": 1.8},
        "170": {"name": "170 💎", "price": 3.5},
        "255": {"name": "255 💎", "price": 6.0},
        "weeklypass": {"name": "Weekly Diamond Pass 💎", "price": 2.6},
        "twilight": {"name": "Twilight Pass ✨ 💎", "price": 11.0}
    }
    await display_payment_page(update, context, "mobilelegends", package, packages)

async def display_payment_page(update: Update, context: ContextTypes.DEFAULT_TYPE, game: str, package: str, packages: dict) -> None:
    """دالة مساعدة لعرض صفحة الدفع."""
    if package not in packages:
        await update.callback_query.answer("❌ باقة غير صحيحة!")
        return
    
    pkg = packages[package]
    escaped_price = escape_html(f'${pkg["price"]:.2f}')
    
    message = (
        f"🎮 <b>{escape_html(pkg['name'])}</b>\n\n"
        f"💰 <b>السعر:</b> {escaped_price}\n\n"
        f"❓ <b>هل تريد شراء هذه الباقة\u061f</b>\n\n"
        f"✅ اضغط على 'نعم، شراء' للمتابعة\n"
        f"⚠️ سيتم خصم المبلغ من محفظتك"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ نعم، شراء", callback_data=f"confirm_{game}_{package}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_to_{game}")]
    ]
    
    await edit_or_reply_message(update, message, keyboard)


    """عرض صفحة الدفع لببجي."""
    packages = {
        "60": {"uc": "60", "price": 0.95},
        "120": {"uc": "120", "price": 1.90},
        "325": {"uc": "325", "price": 4.70}
    }
    
    if package not in packages:
        await update.callback_query.answer("❌ باقة غير صحيحة!")
        return
    
    pkg = packages[package]
    escaped_price = escape_html(f'${pkg["price"]:.2f}')
    message = (
        f"💸 <b>ببجي - {escape_html(pkg['uc'])} UC</b>\n\n"
        f"💰 <b>السعر:</b> {escaped_price}\n\n"
        f"❓ <b>هل تريد شراء هذه الباقة\u061f</b>\n\n"
        f"✅ اضغط على 'نعم، شراء' للمتابعة\n"
        f"⚠️ سيتم خصم المبلغ من محفظتك"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ نعم، شراء", callback_data=f"confirm_pubg_{package}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_pubg")]
    ]
    
    try:
        await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest:
        await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def confirm_game_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تأكيد شراء باقة لعبة - فحص الرصيد وخصمه ثم طلب ID."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # استخراج اللعبة والباقة من callback_data
    parts = data.split('_')
    game = parts[1]
    package = parts[2]
    
    # تحديد الباقات والأسعار
    if game == "freefire":
        packages = {
            "100": {"name": "فري فاير - 100 الماسة", "price": 1.00},
            "210": {"name": "فري فاير - 210 الماسة", "price": 2.00},
            "520": {"name": "فري فاير - 520 الماسة", "price": 5.00},
            "1080": {"name": "فري فاير - 1080 الماسة", "price": 10.00}
        }
        id_label = "ID فري فاير"
    elif game == "pubg":
        packages = {
            "60": {"name": "ببجي - 60 UC", "price": 0.95},
            "120": {"name": "ببجي - 120 UC", "price": 1.90},
            "325": {"name": "ببجي - 325 UC", "price": 4.70}
        }
        id_label = "ID ببجي"
    elif game == "jawaker":
        packages = {
            "10000": {"name": "جواكر - 10000 ♣️", "price": 1.5},
            "red": {"name": "جواكر - مسرع الاحمر ♦️", "price": 2.0},
            "black": {"name": "جواكر - مسرع اسود ♣️", "price": 17.0},
            "blue": {"name": "جواكر - مسرع ازرق 🏄‍♂️", "price": 9.0}
        }
        id_label = "ID جواكر"
    elif game == "fcmobile":
        packages = {
            "99s": {"name": "FC Mobile - 99 🥈", "price": 1.5},
            "499s": {"name": "FC Mobile - 499 🥈", "price": 7.5},
            "999s": {"name": "FC Mobile - 999 🥈", "price": 14.0},
            "100p": {"name": "FC Mobile - 100 point 🪙", "price": 1.5},
            "500p": {"name": "FC Mobile - 500 point 🪙", "price": 7.5},
            "1070p": {"name": "FC Mobile - 1070 point 🪙", "price": 14.0}
        }
        id_label = "ID FC Mobile"
    elif game == "cod":
        packages = {
            "88": {"name": "Call of Duty - 88 🪙", "price": 1.5},
            "460": {"name": "Call of Duty - 460 🪙", "price": 7.0},
            "bp": {"name": "Call of Duty - Battle Pass 💎💫", "price": 3.5},
            "bpb": {"name": "Call of Duty - Battle Pass Blunde 💪", "price": 8.0}
        }
        id_label = "ID Call of Duty"
    elif game == "wildrift":
        packages = {
            "425": {"name": "Wild Rift - 425 🪙", "price": 6.0},
            "stella": {"name": "Wild Rift - STELLA CORN", "price": 6.5},
            "1000": {"name": "Wild Rift - 1000 🪙", "price": 14.0}
        }
        id_label = "ID Wild Rift"
    elif game == "aoe":
        packages = {
            "99": {"name": "Age Of Empires - 99 🪙", "price": 1.3},
            "499": {"name": "Age Of Empires - 499 🪙", "price": 6.5},
            "999": {"name": "Age Of Empires - 999 🪙", "price": 12.5}
        }
        id_label = "ID Age Of Empires"
    elif game == "hok":
        packages = {
            "400": {"name": "Honor of Kings - 400 💸", "price": 6.0},
            "800": {"name": "Honor of Kings - 800 💸", "price": 12.0}
        }
        id_label = "ID Honor of Kings"
    elif game == "lordsmobile":
        packages = {
            "195": {"name": "Lords Mobile - 195 💎", "price": 2.5},
            "395": {"name": "Lords Mobile - 395 💎", "price": 6.5},
            "785": {"name": "Lords Mobile - 785 💎", "price": 11.0},
            "weekly": {"name": "Lords Mobile - أسبوعية 💎", "price": 2.5},
            "monthly": {"name": "Lords Mobile - شهرية 💎", "price": 27.0}
        }
        id_label = "ID Lords Mobile"
    elif game == "genshin":
        packages = {
            "60": {"name": "GENSHIN IMPACT - 60 🔮", "price": 1.0},
            "330": {"name": "GENSHIN IMPACT - 330 🔮", "price": 5.0},
            "moon": {"name": "GENSHIN IMPACT - القمر ويكلين 🔮", "price": 5.0},
            "1090": {"name": "GENSHIN IMPACT - 1090 🔮", "price": 16.0}
        }
        id_label = "ID GENSHIN IMPACT"
    elif game == "mobilelegends":
        packages = {
            "56": {"name": "Mobile Legends - 56 💎", "price": 1.4},
            "86": {"name": "Mobile Legends - 86 💎", "price": 1.8},
            "170": {"name": "Mobile Legends - 170 💎", "price": 3.5},
            "255": {"name": "Mobile Legends - 255 💎", "price": 6.0},
            "weeklypass": {"name": "Mobile Legends - Weekly Diamond Pass 💎", "price": 2.6},
            "twilight": {"name": "Mobile Legends - Twilight Pass ✨ 💎", "price": 11.0}
        }
        id_label = "ID Mobile Legends"
    else:
        await query.edit_message_text("❌ لعبة غير صحيحة!")
        return ConversationHandler.END
    
    if package not in packages:
        await query.edit_message_text("❌ باقة غير صحيحة!")
        return ConversationHandler.END
    
    pkg = packages[package]
    price = pkg["price"]
    
    # فحص رصيد المحفظة
    wallet_balance = await get_user_wallet(user_id)
    
    if wallet_balance < price:
        message = (
            f"❌ <b>رصيد غير كاف!</b>\n\n"
            f"رصيدك الحالي: {escape_html(f'${wallet_balance:.2f}')}\n"
            f"المبلغ المطلوب: {escape_html(f'${price:.2f}')}\n\n"
            f"يرجى شحن محفظتك أولاً."
        )
        keyboard = [
            [InlineKeyboardButton("💰 شحن المحفظة", callback_data="wallet")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_to_{game}")]
        ]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    # خصم المبلغ من المحفظة
    new_balance = wallet_balance - price
    await update_user_wallet(user_id, new_balance, query.from_user.username)
    
    # حفظ بيانات الطلب في context لاستخدامها بعد إدخال ID
    context.user_data['pending_game_order'] = {
        'game': game,
        'package': package,
        'pkg_info': pkg,
        'price': price,
        'new_balance': new_balance
    }
    
    # طلب ID من المستخدم
    message = (
        f"✅ <b>تم خصم المبلغ بنجاح!</b>\n\n"
        f"💰 المبلغ: {escape_html(f'${price:.2f}')}\n"
        f"💳 رصيدك الجديد: {escape_html(f'${new_balance:.2f}')}\n\n"
        f"🎮 <b>الآن، ارسل {escape_html(id_label)} الخاص بك:</b>\n"
        f"✏️ اكتب الـ ID وارسله في رسالة نصية."
    )
    
    await query.edit_message_text(message, parse_mode=ParseMode.HTML)
    
    # الانتقال إلى حالة استقبال ID
    return GAME_ID_INPUT
    """تأكيد شراء باقة لعبة - فحص الرصيد وخصمه ثم طلب ID."""
    user_id = update.effective_user.id
    
    # تحديد السعر حسب اللعبة والباقة
    if game == "freefire":
        packages = {
            "100": {"name": "فري فاير - 100 الماسة", "price": 1.00, "diamonds": "100"},
            "210": {"name": "فري فاير - 210 الماسة", "price": 2.00, "diamonds": "210"},
            "520": {"name": "فري فاير - 520 الماسة", "price": 5.00, "diamonds": "520"},
            "1080": {"name": "فري فاير - 1080 الماسة", "price": 10.00, "diamonds": "1080"}
        }
    elif game == "pubg":
        packages = {
            "60": {"name": "ببجي - 60 UC", "price": 0.95, "uc": "60"},
            "120": {"name": "ببجي - 120 UC", "price": 1.90, "uc": "120"},
            "325": {"name": "ببجي - 325 UC", "price": 4.70, "uc": "325"}
        }
    else:
        await update.callback_query.answer("❌ لعبة غير صحيحة!")
        return
    
    if package not in packages:
        await update.callback_query.answer("❌ باقة غير صحيحة!")
        return
    
    pkg = packages[package]
    price = pkg["price"]
    
    # فحص رصيد المحفظة
    wallet_balance = await get_user_wallet(user_id)
    
    if wallet_balance < price:
        message = (
            f"❌ <b>رصيد غير كاف!</b>\n\n"
            f"رصيدك الحالي: ${wallet_balance:.2f}\n"
            f"المبلغ المطلوب: ${price:.2f}\n\n"
            f"يرجى شحن محفظتك أولاً."
        )
        keyboard = [
            [InlineKeyboardButton("💰 شحن المحفظة", callback_data="wallet")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_to_{game}")]
        ]
        try:
            await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest:
            await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        return
    
    # خصم المبلغ من المحفظة
    new_balance = wallet_balance - price
    await update_user_wallet(user_id, new_balance, update.effective_user.username)
    
    # حفظ بيانات الطلب في context لاستخدامها بعد إدخال ID
    context.user_data['pending_game_order'] = {
        'game': game,
        'package': package,
        'pkg_info': pkg,
        'price': price,
        'new_balance': new_balance
    }
    
    # طلب ID من المستخدم
    if game == "freefire":
        id_label = "ID فري فاير"
    else:
        id_label = "ID ببجي"
    
    message = (
        f"✅ <b>تم خصم المبلغ بنجاح!</b>\n\n"
        f"💰 المبلغ: {escape_html(f'${price:.2f}')}\n"
        f"💳 رصيدك الجديد: {escape_html(f'${new_balance:.2f}')}\n\n"
        f"🎮 <b>الآن، ارسل {escape_html(id_label)} الخاص بك:</b>\n"
        f"✏️ اكتب الـ ID وارسله في رسالة نصية."
    )
    
    try:
        await update.callback_query.edit_message_text(message, parse_mode=ParseMode.HTML)
    except BadRequest:
        await update.callback_query.message.reply_text(message, parse_mode=ParseMode.HTML)
    
    # الانتقال إلى حالة استقبال ID
    return GAME_ID_INPUT

# تم حذف هذه الدالة المكررة لتوحيد منطق الشراء في complete_purchase



async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض الفئات."""
    categories = await get_all_categories_db(active_only=True)
    
    if not categories:
        message = "لا توجد فئات متاحة حالياً."
        keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]]
    else:
        message = "🛍️ اختر الفئة التي تريد تصفحها:"
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(cat['name'], callback_data=f"cat_{cat['category_id']}")])
        keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")])
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_subcategories(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: str) -> None:
    """عرض الفئات الفرعية."""
    subcategories = await get_subcategories_by_category_db(category_id, active_only=True)
    
    if not subcategories:
        # لا توجد فئات فرعية، عرض المنتجات مباشرة
        await show_products(update, context, category_id, "category")
        return
    
    message = "اختر الفئة الفرعية:"
    keyboard = []
    for subcat in subcategories:
        keyboard.append([InlineKeyboardButton(subcat['icon'] + " " + subcat['name'], callback_data=f"subcat_{subcat['subcategory_id']}")])
    
    # تحديد زر الرجوع بناءً على الفئة
    back_callback = "show_games" if category_id == "cat_games" else "show_activations" if category_id == "cat_activations" else "main_menu"
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=back_callback)])
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_servers(update: Update, context: ContextTypes.DEFAULT_TYPE, subcategory_id: str) -> None:
    """عرض السيرفرات."""
    servers = await get_servers_by_subcategory_db(subcategory_id, active_only=True)
    
    if not servers:
        # لا توجد سيرفرات، عرض المنتجات مباشرة
        await show_products(update, context, subcategory_id, "subcategory")
        return
    
    message = "اختر السيرفر:"
    keyboard = []
    for server in servers:
        keyboard.append([InlineKeyboardButton(server['name'], callback_data=f"server_{server['server_id']}")])
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"subcat_{subcategory_id}")])
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE, parent_id: str, parent_type: str) -> None:
    """عرض المنتجات."""
    products = await get_products_by_parent_db(parent_id, parent_type, active_only=True)
    
    if not products:
        message = "لا توجد منتجات متاحة في هذه الفئة."
        keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="categories")]]
    else:
        message = "اختر المنتج:"
        keyboard = []
        for prod in products:
            keyboard.append([InlineKeyboardButton(f"{prod['name']} - ${prod['price']:.2f}", callback_data=f"product_{prod['product_id']}")])
        
        if parent_type == "server":
            keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"server_{parent_id}")])
        elif parent_type == "subcategory":
            # الرجوع للفئة المناسبة
            if parent_id.startswith("act_"):
                keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="show_activations")])
            else:
                keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"subcat_{parent_id}")])
        else:
            # إذا كان الأب هو فئة مباشرة (مثل أرقام التفعيلات أحياناً)
            back_call = "show_activations" if parent_id == "cat_activations" else "show_games" if parent_id == "cat_games" else "main_menu"
            keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=back_call)])
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_product_details(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: str) -> None:
    """عرض تفاصيل المنتج مع الصورة وزر الشراء."""
    product = await get_product_by_id_db(product_id)
    
    if not product:
        await update.callback_query.answer("❌ المنتج غير موجود.", show_alert=True)
        return

    # بناء الرسالة
    message = f"📦 <b>{escape_html(product['name'])}</b>\n\n"
    message += f"💰 السعر: <b>${product['price']:.2f}</b>\n"
    if product['description']:
        message += f"📝 الوصف: {escape_html(product['description'])}\n\n"
    
    # تحديد وجهة الرجوع بناءً على المنتج
    back_data = "show_activations" if "prod_" in product_id else "show_games"
    
    # بناء لوحة المفاتيح
    keyboard = [
        [InlineKeyboardButton("🛒 شراء الآن", callback_data=f"buy_now_{product_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=back_data)]
    ]
    
    # تحديد طريقة الإرسال (صورة أو نص)
    if product.get('icon'):
        # إذا كان هناك أيقونة، نستخدمها كـ caption للصورة
        caption = message
        
        # محاولة إرسال الصورة
        try:
            # يجب أن يكون هناك ملف صورة حقيقي، لكننا سنستخدم الأيقونة كـ caption مؤقتاً
            # إذا كان لديك رابط صورة حقيقي، يجب استخدامه هنا
            # بما أننا لا نملك رابط صورة، سنرسل رسالة نصية مع الأيقونة في البداية
            
            # نستخدم الأيقونة في بداية الرسالة
            message = f"{product['icon']} " + message
            
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            
        except BadRequest:
            # إذا فشل التعديل (لأن الرسالة قديمة أو تم تغيير نوعها)، نرسل رسالة جديدة
            await update.callback_query.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
    else:
        # إذا لم يكن هناك أيقونة، نرسل رسالة نصية عادية
        try:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
        except BadRequest:
            await update.callback_query.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: str) -> None:
    """إضافة منتج للسلة."""
    user_id = update.effective_user.id
    product = await get_product_by_id_db(product_id)
    
    if not product:
        await update.callback_query.answer("❌ المنتج غير موجود.", show_alert=True)
        return
    
    await add_to_cart_db(user_id, product_id, product['name'], product['price'])
    await update.callback_query.answer(f"✅ تم إضافة {product['name']} إلى السلة!", show_alert=True)

# --- دوال الشراء مع دعم معرفات الألعاب المحفوظة ---

async def request_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """طلب معرف اللعبة مع خيار استخدام المعرفات المحفوظة."""
    query = update.callback_query
    # استخراج معرف المنتج من أنماط مختلفة (buy_now_, buy_cart_item_, buy_game_package_)
    product_id = query.data
    # جدول التحويل: prefix -> db_prefix للمعرفات التي لها تعارض
    prefix_db_map = {
        "buy_freefire_":      "",
        "buy_pubg_":          "pubg_",
        "buy_jawaker_":       "",
        "buy_fcmobile_":      "",
        "buy_cod_":           "",
        "buy_wildrift_":      "",
        "buy_aoe_":           "aoe_",
        "buy_hok_":           "",
        "buy_lordsmobile_":   "",
        "buy_genshin_":       "genshin_",
        "buy_mobilelegends_": "",
        "buy_now_":           "",
        "buy_cart_item_":     "",
    }
    for prefix, db_prefix in prefix_db_map.items():
        if product_id.startswith(prefix):
            raw_id = product_id[len(prefix):]
            product_id = db_prefix + raw_id
            break
    
    product = await get_product_by_id_db(product_id)
    if not product:
        await query.answer("❌ المنتج غير موجود.", show_alert=True)
        return ConversationHandler.END
    
    context.user_data['purchase_product_id'] = product_id
    context.user_data['purchase_product_name'] = product['name']
    context.user_data['purchase_price'] = product['price']
    
    user_id = update.effective_user.id
    
    # طلب إدخال معرف جديد مباشرة لجميع المنتجات
    await query.message.reply_text(
        f"🎮 يرجى إرسال معرف اللاعب (ID) الخاص بك:\n\n"
        f"المنتج: <b>{escape_html(product['name'])}</b>\n"
        f"السعر: ${product['price']:.2f}\n\n"
        f"لإلغاء العملية، أرسل /cancel",
        parse_mode=ParseMode.HTML
    )
    return ASK_GAME_ID

async def handle_saved_game_id_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة اختيار معرف لعبة محفوظ."""
    query = update.callback_query
    
    if query.data == "enter_new_game_id":
        await query.message.reply_text(
            "🎮 يرجى إرسال معرف اللعبة الجديد:\n\nلإلغاء العملية، أرسل /cancel"
        )
        return ASK_GAME_ID
    elif query.data == "cancel_purchase":
        await query.message.reply_text("❌ تم إلغاء عملية الشراء.")
        context.user_data.clear()
        return ConversationHandler.END
    elif query.data.startswith("use_saved_id_"):
        saved_id_record_id = int(query.data.replace("use_saved_id_", ""))
        user_id = update.effective_user.id
        
        # جلب المعرف المحفوظ
        saved_ids = await get_saved_game_ids_db(user_id)
        selected_id = next((sid for sid in saved_ids if sid['id'] == saved_id_record_id), None)
        
        if not selected_id:
            await query.answer("❌ المعرف غير موجود.", show_alert=True)
            return ConversationHandler.END
        
        # استخدام المعرف المحفوظ لإتمام الشراء
        game_id = selected_id['game_id']
        await complete_purchase(update, context, game_id, is_callback=True)
        return ConversationHandler.END

async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال معرف اللعبة (نص، أرقام، رموز) وإتمام الشراء."""
    # استقبال النص كما هو لضمان قبول الرموز والأحرف
    game_id = update.message.text.strip() if update.message.text else ""
    
    if not game_id:
        await update.message.reply_text("❌ يرجى إرسال معرف صحيح.")
        return GAME_ID_INPUT

    # إتمام الشراء مباشرة
    await complete_purchase(update, context, game_id)
    return ConversationHandler.END

async def handle_save_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة قرار حفظ معرف اللعبة."""
    query = update.callback_query
    game_id = context.user_data.get('temp_game_id')
    user_id = update.effective_user.id
    
    if query.data == "save_game_id_yes":
        # حفظ المعرف
        product_name = context.user_data.get('purchase_product_name', '')
        game_name = product_name.split()[0]
        await save_game_id_db(user_id, game_name, game_id, is_default=True)
        await query.answer("✅ تم حفظ المعرف بنجاح!", show_alert=True)
    
    # إتمام الشراء
    await complete_purchase(update, context, game_id, is_callback=True)
    return ConversationHandler.END

async def complete_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, is_callback: bool = False):
    """إتمام عملية الشراء."""
    user_id = update.effective_user.id if is_callback else update.message.from_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    product_id = context.user_data.get('purchase_product_id')
    product_name = context.user_data.get('purchase_product_name')
    price = context.user_data.get('purchase_price')
    
    # إذا لم يتم العثور على السعر، نستخدم سعر الباقة من بيانات الطلب المعلقة
    if price is None:
        order_data = context.user_data.get('pending_game_order')
        if order_data:
            price = order_data.get('price')
    
    # الحل الاحتياطي: جلب السعر من قاعدة البيانات باستخدام product_id
    if price is None and product_id:
        product = await get_product_by_id_db(product_id)
        if product:
            price = product.get('price')
            product_name = product.get('name') # تحديث الاسم أيضاً
    
    # التحقق من product_name وتعيينه إلى سلسلة فارغة إذا كان None
    if product_name is None:
        product_name = ""
    
    # التحقق النهائي من أن السعر رقمي
    if price is None or not isinstance(price, (int, float)):
        logger.error(f"Price is None or not numeric for user {user_id}. Context: {context.user_data}")
        # رسالة خطأ أكثر دقة
        error_msg = "❌ حدث خطأ في معالجة السعر. يرجى المحاولة مرة أخرى من البداية."
        if update.callback_query:
            await update.callback_query.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        context.user_data.clear()
        return
    
    # فحص الرصيد وخصمه
    user_wallet = await get_user_wallet(user_id)
    if user_wallet < price:
        error_msg = f"❌ رصيدك غير كافٍ. السعر: ${price:.2f}، رصيدك: ${user_wallet:.2f}"
        if is_callback:
            await update.callback_query.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return

    new_balance = user_wallet - price
    await update_user_wallet(user_id, new_balance, username)

    # إضافة إلى سجل المشتريات
    purchase_id = await add_purchase_history_db(
        int(user_id), 
        str(username), 
        str(product_name), 
        str(game_id), 
        float(price)
    )
    
    # إرسال إشعار للمسؤول
    if ADMIN_USER_ID:
        # إرسال رسالة نصية مجردة تماماً للأدمن لضمان الوصول 100%
        admin_message = (
            f"🛒 طلب شراء جديد!\n\n"
            f"👤 المستخدم: {username} (ID: {user_id})\n"
            f"📦 المنتج: {product_name}\n"
            f"🎮 معرف اللعبة: {game_id}\n"
            f"💰 المبلغ: ${price:.2f}\n\n"
            f"✅ للتأكيد (اضغط للنسخ):\n<code>/admin_confirm_shipped {purchase_id}</code>"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text=admin_message)
            logger.info(f"Admin {ADMIN_USER_ID} notified about new purchase from {username}.")
        except Exception as e:
            logger.error(f"Critical: Failed to send admin notification: {str(e)}")
    
    # إرسال رسالة تأكيد للمستخدم
    confirmation_message = (
        f"✅ تم استلام طلبك بنجاح!\n\n"
        f"المنتج: <b>{escape_html(product_name)}</b>\n"
        f"المعرف: <code>{escape_html(game_id)}</code>\n"
        f"تم خصم ${price:.2f} من محفظتك. سيتم تنفيذ الطلب قريباً وإرسال إشعار لك."
    )
    
    # إضافة زر واتساب إذا كان المنتج يخص أرقام التفعيلات
    reply_markup = None
    if "رقم" in product_name or "تفعيل" in product_name:
        whatsapp_url = "https://wa.me/963940902808"
        keyboard = [[InlineKeyboardButton("💬 استلم رقمك عبر واتساب", url=whatsapp_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        confirmation_message += "\n\n📩 يرجى الضغط على الزر أدناه للتواصل مع المسؤول واستلام رقمك."

    if is_callback:
        await update.callback_query.message.reply_text(confirmation_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(confirmation_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    # مسح بيانات المحادثة
    context.user_data.clear()

# سيتم إكمال الملف في الجزء الثاني...

# --- دوال المحفظة والإيداع ---

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض المحفظة."""
    user_id = update.effective_user.id
    user_wallet = await get_user_wallet(user_id)
    
    # بناء لوحة المفاتيح بناءً على طرق الدفع المتاحة
    keyboard = []
    for method_key, method_data in PAYMENT_METHODS.items():
        if method_data.get('enabled', False):
            keyboard.append([InlineKeyboardButton(
                method_data['name'], 
                callback_data=f"deposit_{method_key}"
            )])
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")])
    
    escaped_wallet = escape_html(f'${user_wallet:.2f}')
    message = f"💰 محفظتك\n\nرصيدك الحالي: <b>{escaped_wallet}</b>\n\nاختر طريقة الإيداع:"
    
    if update.message:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
        except BadRequest:
            await update.callback_query.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )

async def sham_cash_deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية إيداع شام كاش."""
    sham_code = PAYMENT_METHODS.get('sham_cash', {}).get('code', 'b441bd2368ed511aebd2f9e79723936d')
    message = (
        "💰 إيداع شام كاش\n\n"
        "لإتمام التحويل استخدم الكود التالي في تطبيق شام كاش:\n\n"
        "🔑 <b>كود الاستلام:</b>\n"
        f"<code>{escape_html(sham_code)}</code>\n\n"
        "📌 <b>خطوات التحويل:</b>\n"
        "1️⃣ افتح تطبيق شام كاش\n"
        "2️⃣ اختر <b>تحويل</b>\n"
        "3️⃣ الصق الكود أعلاه في خانة المستلم\n"
        "4️⃣ أدخل المبلغ وأكمل التحويل\n\n"
        "بعد التحويل، أرسل <b>المبلغ</b> الذي حوّلته:\n"
        "(مثال: 5 أو 10.50)\n\n"
        "لإلغاء العملية، أرسل /cancel"
    )
    await update.callback_query.message.reply_text(message, parse_mode=ParseMode.HTML)
    await update.callback_query.answer()
    return SHAM_CASH_AMOUNT

async def sham_cash_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال مبلغ إيداع شام كاش."""
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("❌ يرجى إدخال مبلغ صحيح أكبر من الصفر.")
            return SHAM_CASH_AMOUNT
        context.user_data['amount'] = amount
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال المبلغ كأرقام فقط. (مثال: 5 أو 10.50)")
        return SHAM_CASH_AMOUNT
    await update.message.reply_text(
        f"✅ تم استلام المبلغ: <b>${amount:.2f}</b>\n\n"
        "الآن أرسل <b>صورة إثبات التحويل</b> من تطبيق شام كاش.\n\n"
        "لإلغاء العملية، أرسل /cancel",
        parse_mode=ParseMode.HTML
    )
    return SHAM_CASH_PHOTO

async def sham_cash_deposit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال صورة إثبات التحويل لشام كاش."""
    if not update.message.photo:
        await update.message.reply_text(
            "❌ يرجى إرسال <b>صورة</b> إثبات التحويل وليس نصاً.\n"
            "لإلغاء العملية، أرسل /cancel",
            parse_mode=ParseMode.HTML
        )
        return SHAM_CASH_PHOTO
    amount = context.user_data.get('amount')
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    if not amount:
        await update.message.reply_text("❌ حدث خطأ. يرجى البدء من جديد.")
        return ConversationHandler.END
    photo_id = update.message.photo[-1].file_id
    transaction_id = f"SHAM_{user_id}_{int(amount*100)}"
    await add_pending_payment(user_id, username, amount, transaction_id, "Sham Cash", context)
    # إرسال الصورة للأدمن
    if ADMIN_USER_ID:
        try:
            await context.bot.send_photo(
                chat_id=ADMIN_USER_ID,
                photo=photo_id,
                caption=(
                    f"🖼️ إثبات تحويل شام كاش\n\n"
                    f"👤 المستخدم: {username} (ID: {user_id})\n"
                    f"💰 المبلغ: ${amount:.2f}\n"
                    f"✅ للتأكيد:\n/admin_confirm_deposit {user_id} {amount:.2f}"
                )
            )
        except Exception as e:
            logger.error(f"Failed to send photo to admin: {e}")
    await update.message.reply_text(
        f"✅ تم استلام طلب الإيداع بنجاح!\n\n"
        f"💳 طريقة الدفع: شام كاش\n"
        f"💰 المبلغ: ${amount:.2f}\n\n"
        "سيتم مراجعة الطلب من قبل المسؤول وإضافة رصيدك في أقرب وقت ممكن. 🙏",
        parse_mode=ParseMode.HTML
    )
    context.user_data.clear()
    return ConversationHandler.END




async def syriatel_code_deposit_start(update, context):
    """بدء عملية إيداع سيرياتيل كاش - رمز."""
    method_data = PAYMENT_METHODS.get('syriatel_cash_code', {})
    code = method_data.get('code', 'غير متوفر')
    message = (
        "🔑 إيداع سيرياتيل كاش - رمز\n\n"
        "يرجى تحويل المبلغ المطلوب باستخدام الرمز التالي:\n"
        "<b>الرمز: <code>" + escape_html(code) + "</code></b>\n\n"
        "📌 خطوات التحويل:\n"
        "1️⃣ اذهب إلى تطبيق سيرياتيل كاش\n"
        "2️⃣ اختر تحويل - ثم تحويل برمز\n"
        "3️⃣ أدخل الرمز: <code>" + escape_html(code) + "</code>\n"
        "4️⃣ أدخل المبلغ المطلوب\n\n"
        "بعد إتمام التحويل، أرسل لنا المبلغ الذي حوّلته:\n\n"
        "لإلغاء العملية، أرسل /cancel"
    )
    await update.callback_query.message.reply_text(message, parse_mode=ParseMode.HTML)
    await update.callback_query.answer()
    return SYRIATEL_CODE_AMOUNT


async def syriatel_code_deposit_amount(update, context):
    """استقبال مبلغ الإيداع عبر الرمز."""
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("❌ يرجى إدخال مبلغ صحيح أكبر من الصفر.")
            return SYRIATEL_CODE_AMOUNT
        context.user_data['amount'] = amount
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال المبلغ كأرقام فقط (مثال: 5.00)")
        return SYRIATEL_CODE_AMOUNT
    await update.message.reply_text(
        "✅ تم استلام المبلغ.\n\n"
        "الآن أرسل رقم العملية (Transaction ID) الذي ظهر لك بعد التحويل.\n\n"
        "لإلغاء العملية، أرسل /cancel",
        parse_mode=ParseMode.HTML
    )
    return SYRIATEL_CODE_TRANSACTION_ID


async def syriatel_code_transaction_id(update, context):
    """استقبال رقم عملية التحويل برمز سيرياتيل."""
    transaction_id = update.message.text
    amount = context.user_data.get('amount')
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    if not amount:
        await update.message.reply_text("❌ حدث خطأ في تحديد المبلغ. يرجى البدء من جديد.")
        return ConversationHandler.END
    await add_pending_payment(user_id, username, amount, transaction_id, "Syriatel Cash Code", context)
    await update.message.reply_text(
        "✅ تم استلام طلب الإيداع بنجاح!\n\n"
        "💳 طريقة الدفع: سيرياتيل كاش - رمز\n"
        f"💰 المبلغ: ${amount:.2f}\n"
        f"🔢 رقم العملية: <code>{escape_html(transaction_id)}</code>\n\n"
        "سيتم مراجعة الطلب وإضافة رصيدك في أقرب وقت ممكن. 🙏",
        parse_mode=ParseMode.HTML
    )
    context.user_data.clear()
    return ConversationHandler.END



async def cancel_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء عملية الإيداع."""
    await update.message.reply_text("❌ تم إلغاء عملية الإيداع.")
    context.user_data.clear()
    return ConversationHandler.END

# --- دوال المسؤول ---

async def admin_confirm_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تأكيد طلب إيداع."""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للمسؤول فقط.")
        return

    try:
        _, user_id_str, amount_str = update.message.text.split()
        user_id = int(user_id_str)
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text("❌ صيغة الأمر غير صحيحة. الاستخدام: <code>/admin_confirm_deposit <user_id> <amount></code>", parse_mode=ParseMode.HTML)
        return

    await update_user_wallet(user_id, amount)
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ تم تأكيد إيداعك بنجاح!\n\nتم إضافة ${amount:.2f} إلى محفظتك. رصيدك الحالي: ${await get_user_wallet(user_id):.2f}",
            parse_mode=ParseMode.HTML
        )
        await update.message.reply_text(f"✅ تم تأكيد الإيداع وإضافة ${amount:.2f} للمستخدم {user_id}.")
    except Exception as e:
        await update.message.reply_text(f"✅ تم تأكيد الإيداع، ولكن فشل إرسال إشعار للمستخدم {user_id}. الخطأ: {str(e)}")

async def admin_confirm_shipped(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تأكيد شحن طلب."""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للمسؤول فقط.")
        return

    try:
        _, purchase_id = update.message.text.split()
    except ValueError:
        await update.message.reply_text("❌ صيغة الأمر غير صحيحة. الاستخدام: <code>/admin_confirm_shipped <purchase_id></code>", parse_mode=ParseMode.HTML)
        return

    shipped_at = datetime.now().isoformat()
    purchase = await get_purchase_by_id_db(purchase_id)
    
    if not purchase:
        await update.message.reply_text("❌ لم يتم العثور على هذا الطلب.")
        return

    await update_purchase_status_db(purchase_id, "Shipped", shipped_at)
    
    # إرسال رسالة للمستخدم
    try:
        await context.bot.send_message(
            chat_id=purchase['user_id'],
            text="✅ تمت عملية الشحن بنجاح!"
        )
    except Exception as e:
        logger.error(f"Failed to notify user {purchase['user_id']} about shipping: {e}")

    await update.message.reply_text(f"✅ تم تأكيد شحن الطلب {purchase_id} وإرسال إشعار للمستخدم.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض الإحصائيات."""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للمسؤول فقط.")
        return

    total_users = await get_total_users_db()
    new_users_today = await get_new_users_today_db()
    active_users_24h = await get_active_users_last_24_hours_db()

    stats_message = (
        f"📊 إحصائيات البوت\n\n"
        f"👥 إجمالي المستخدمين: <b>{total_users}</b>\n"
        f"🆕 مستخدمون جدد اليوم: <b>{new_users_today}</b>\n"
        f"⚡ مستخدمون نشطون (آخر 24 ساعة): <b>{active_users_24h}</b>\n"
    )

    await update.message.reply_text(stats_message, parse_mode=ParseMode.HTML)

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية البث."""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للمسؤول فقط.")
        return ConversationHandler.END

    await update.message.reply_text(
        "يرجى إرسال الرسالة التي تريد بثها لجميع المستخدمين.\n\n"
        "يمكنك استخدام تنسيق MarkdownV2.\n"
        "لإلغاء العملية، أرسل /cancel",
        parse_mode=ParseMode.HTML
    )
    return BROADCAST_MESSAGE

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إرسال رسالة البث."""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للمسؤول فقط.")
        return ConversationHandler.END

    message_to_send = update.message.text
    user_ids = await get_all_user_ids_db()
    
    sent_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message_to_send, parse_mode=ParseMode.HTML)
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user_id}: {str(e)}")
            failed_count += 1

    await update.message.reply_text(
        f"✅ تم الانتهاء من عملية البث.\n\n"
        f"تم الإرسال بنجاح إلى: <b>{sent_count}</b> مستخدم.\n"
        f"فشل الإرسال إلى: <b>{failed_count}</b> مستخدم.",
        parse_mode=ParseMode.HTML
    )
    
    return ConversationHandler.END

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء البث."""
    await update.message.reply_text("❌ تم إلغاء عملية البث.")
    return ConversationHandler.END

# --- دوال رئيسية ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بدء البوت."""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    await update_user_activity_db(user_id)

    if GROUP_ID and GROUP_JOIN_LINK:
        try:
            member = await context.bot.get_chat_member(GROUP_ID, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                await send_channel_join_message(update, user_id, first_name, context)
                return
        except Exception as e:
            logger.error(f"Error checking channel membership for user {user_id}: {e}")
            await send_channel_join_message(update, user_id, first_name, context)
            return

    message = f"مرحباً بك في <b>{escape_html(WEBSITE_NAME)}</b>!\n\n{escape_html(WEBSITE_SLOGAN)}"
    
    if update.message:
        await update.message.reply_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML
            )
        except BadRequest:
            await update.callback_query.message.reply_text(
                message,
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.HTML
            )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الرسائل النصية."""
    await update_user_activity_db(update.effective_user.id)
    
    text = update.message.text
    
    if text == "🛒 سلة المشتريات":
        await show_cart(update, context)
    elif text == "📋 طلباتي":
        await show_orders(update, context)
    elif text == "ℹ️ معلومات عنا":
        await show_about_us(update, context)
    elif text == "📞 التواصل معنا":
        await show_contact_info(update, context)
    elif text == "💰 محفظتي":
        await wallet(update, context)
    elif "الألعاب" in text:
        await show_games(update, context)
    elif "أرقام التفعيلات" in text or "تفعيل" in text:
        await show_activations(update, context)
    elif text == "🏠 القائمة الرئيسية":
        await start(update, context)
    else:
        await update.message.reply_text("عذراً، لم أفهم طلبك. يرجى استخدام الأزرار في القائمة الرئيسية.")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة ضغطات الأزرار."""
    query = update.callback_query
    data = query.data
    
    await update_user_activity_db(update.effective_user.id)

    if data == "main_menu":
        await start(update, context)
    elif data == "show_cart":
        await show_cart(update, context)
    elif data == "show_orders":
        await show_orders(update, context)
    elif data == "show_about_us":
        await show_about_us(update, context)
    elif data == "show_contact_info":
        await show_contact_info(update, context)
    elif data == "wallet":
        await wallet(update, context)
    elif data == "admin_panel":
        await admin_panel(update, context)
    elif data == "admin_list_categories":
        await admin_list_categories(update, context)
    elif data == "admin_list_products":
        await admin_list_products(update, context)
    elif data == "admin_delete_product_start":
        await admin_delete_product_start(update, context)
    elif data == "show_games":
        await show_games(update, context)
    elif data == "show_activations":
        await show_activations(update, context)
    elif data.startswith("act_"):
        # تفعيل الحسابات - عرض المنتجات تحت الفئة الفرعية
        await show_products(update, context, data, "subcategory")
    elif data == "game_freefire":
        await show_freefire_packages(update, context)
    elif data == "game_pubg":
        await show_pubg_packages(update, context)
    elif data == "game_jawaker":
        await show_jawaker_packages(update, context)
    elif data == "game_fcmobile":
        await show_fcmobile_packages(update, context)
    elif data == "game_cod":
        await show_cod_packages(update, context)
    elif data == "game_wildrift":
        await show_wildrift_packages(update, context)
    elif data == "game_aoe":
        await show_aoe_packages(update, context)
    elif data == "game_hok":
        await show_hok_packages(update, context)
    elif data == "game_lordsmobile":
        await show_lordsmobile_packages(update, context)
    elif data == "game_genshin":
        await show_genshin_packages(update, context)
    elif data == "game_mobilelegends":
        await show_mobilelegends_packages(update, context)
    elif data.startswith("buy_"):
        # توجيه جميع عمليات الشراء لطلب الـ ID أولاً
        await request_game_id(update, context)
    elif data.startswith("back_to_"):
        back_to = data.replace("back_to_", "")
        if back_to == "games":
            await show_games(update, context)
        elif back_to == "freefire":
            await show_freefire_packages(update, context)
        elif back_to == "pubg":
            await show_pubg_packages(update, context)
    else:
        await query.answer("❌ أمر غير معروف.")

# --- دالة main ---

def main() -> None:
    """تشغيل البوت."""
    
    application = Application.builder().token(BOT_TOKEN).build()

    # محادثات إيداع شام كاش
    sham_cash_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(sham_cash_deposit_start, pattern='^deposit_sham_cash$')],
        states={
            SHAM_CASH_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, sham_cash_deposit_amount)],
            SHAM_CASH_PHOTO: [MessageHandler(filters.PHOTO, sham_cash_deposit_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(sham_cash_handler)

    # محادثات إيداع سيرياتيل كاش - رمز
    syriatel_code_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(syriatel_code_deposit_start, pattern='^deposit_syriatel_cash_code$')],
        states={
            SYRIATEL_CODE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, syriatel_code_deposit_amount)],
            SYRIATEL_CODE_TRANSACTION_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, syriatel_code_transaction_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(syriatel_code_handler)

    # محادثات الشراء
    purchase_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(request_game_id, pattern='^buy_')
        ],
        states={
            CHOOSE_SAVED_GAME_ID: [CallbackQueryHandler(handle_saved_game_id_choice)],
            ASK_GAME_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_game_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(purchase_handler)

    # محادثات شراء الألعاب
    game_purchase_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(confirm_game_purchase, pattern='^confirm_freefire_'),
            CallbackQueryHandler(confirm_game_purchase, pattern='^confirm_pubg_')
        ],
        states={
            GAME_ID_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_game_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(game_purchase_handler)

    # محادثات البث
    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel_broadcast)],
        allow_reentry=True
    )
    application.add_handler(broadcast_handler)

    # محادثات إضافة فئة
    add_category_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_category_start, pattern='^admin_add_category$')],
        states={
            ADD_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_category_name)],
            ADD_CATEGORY_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_category_desc)],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_operation)],
        allow_reentry=True
    )
    application.add_handler(add_category_handler)

    # محادثات إضافة منتج
    add_product_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_product_start, pattern='^admin_add_product_start$')],
        states={
            ADD_PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_name)],
            ADD_PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_price)],
            ADD_PRODUCT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_desc)],
            ADD_PRODUCT_CATEGORY: [CallbackQueryHandler(admin_add_product_category, pattern='^addprod_cat_')],
            ADD_PRODUCT_SUBCATEGORY: [CallbackQueryHandler(admin_add_product_subcategory, pattern='^addprod_subcat_')],
            ADD_PRODUCT_SERVER: [CallbackQueryHandler(admin_add_product_server, pattern='^addprod_server_')],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_operation)],
        allow_reentry=True
    )
    application.add_handler(add_product_handler)

    # محادثات تعديل منتج
    edit_product_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_edit_product_start, pattern='^admin_edit_product_start$')],
        states={
            EDIT_PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_product_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_operation)],
        allow_reentry=True
    )
    application.add_handler(edit_product_handler)

    # الأوامر العادية
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("admin_confirm_deposit", admin_confirm_deposit))
    application.add_handler(CommandHandler("admin_confirm_shipped", admin_confirm_shipped))
    application.add_handler(CommandHandler("delete_product", admin_delete_product))

    # معالجة ضغطات الأزرار
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # معالجة الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"🤖 تم تشغيل بوت {WEBSITE_NAME} بنجاح! (النسخة المحسنة)")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    init_db()
    main()
