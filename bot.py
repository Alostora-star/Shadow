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
    save_game_id_db, get_saved_game_ids_db, delete_saved_game_id_db,
    add_coupon_db, get_coupon_db, use_coupon_db, get_all_coupons_db, delete_coupon_db,
    get_total_revenue_db, get_total_orders_db, get_pending_orders_db,
    get_pending_deposits_db, get_top_products_db, get_user_info_db,
    set_user_balance_db, get_revenue_today_db,
    get_exchange_rate_db, set_exchange_rate_db, get_user_currency_db, set_user_currency_db,
    init_referral_tables, add_referral_db, get_referral_stats_db,
    mark_referral_rewarded_db, get_referrer_db, get_referral_reward_db, set_referral_reward_db,
    add_flash_offer_db, get_active_flash_offers_db, get_flash_offer_by_product_db, deactivate_flash_offer_db,
    init_support_table, create_ticket_db, add_ticket_message_db, get_user_tickets_db,
    get_ticket_messages_db, get_ticket_by_id_db, get_open_tickets_db, close_ticket_db,
    request_refund_db, get_pending_refunds_db, process_refund_db,
    get_user_language_db, set_user_language_db,
    set_user_2fa_db, get_user_2fa_db
)

from keyboards import get_main_menu_keyboard, get_back_to_main_keyboard, detect_button
from translations import t, LANGUAGE_NAMES

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
ASK_COUPON = 30
ADD_COUPON_CODE, ADD_COUPON_TYPE, ADD_COUPON_VALUE, ADD_COUPON_USES = range(31, 35)
ADMIN_SET_BALANCE_USER, ADMIN_SET_BALANCE_AMOUNT = range(40, 42)
ADMIN_SET_RATE = 43
SET_CURRENCY = 44
ADD_OFFER_PRODUCT, ADD_OFFER_PRICE, ADD_OFFER_HOURS = range(50, 53)
ADMIN_SET_REF_REWARD = 54
SUPPORT_SUBJECT, SUPPORT_MESSAGE, SUPPORT_REPLY = range(60, 63)
REFUND_REASON = 70
TWO_FA_CONFIRM = 71
CART_CHECKOUT_CONFIRM = 72

# --- دوال مساعدة ---



async def get_user_wallet(user_id: int) -> float:
    """جلب رصيد المحفظة."""
    return await get_user_wallet_db(user_id)


# --- دوال العملات المساعدة ---

async def format_price(user_id: int, usd_amount: float) -> str:
    """تنسيق السعر حسب عملة المستخدم."""
    currency = await get_user_currency_db(user_id)
    if currency == 'SYP':
        rate = await get_exchange_rate_db()
        syp_amount = usd_amount * rate
        return f"{syp_amount:,.0f} ل.س"
    return f"${usd_amount:.2f}"

async def get_price_line(user_id: int, usd_amount: float) -> str:
    """سطر السعر مع كلتا العملتين."""
    currency = await get_user_currency_db(user_id)
    if currency == 'SYP':
        rate = await get_exchange_rate_db()
        syp_amount = usd_amount * rate
        return f"${usd_amount:.2f} — <b>{syp_amount:,.0f} ل.س</b>"
    return f"<b>${usd_amount:.2f}</b>"

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

    if cart:
        keyboard_buttons.append([InlineKeyboardButton("💳 إتمام شراء الكل", callback_data="cart_checkout")])
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

    STATUS_EMOJI = {
        'pending_shipment': '⏳ قيد التنفيذ',
        'shipped': '✅ تم الشحن',
        'completed': '✅ مكتمل',
        'cancelled': '❌ ملغي',
        'pending': '⏳ معلق',
    }

    lang = await get_user_language_db(user_id)
    STATUS_EMOJI["refund_requested"] = t(lang,"status_refund_req")
    STATUS_EMOJI["refunded"]         = t(lang,"status_refunded")
    STATUS_EMOJI["shipped"]          = t(lang,"status_shipped")
    STATUS_EMOJI["Shipped"]          = t(lang,"status_shipped")
    STATUS_EMOJI["completed"]        = t(lang,"status_completed")
    STATUS_EMOJI["cancelled"]        = t(lang,"status_cancelled")
    STATUS_EMOJI["pending_shipment"] = t(lang,"status_pending")
    STATUS_EMOJI["pending"]          = t(lang,"status_pending")

    if not orders:
        message = t(lang,"orders_empty")
    else:
        message = t(lang,"orders_title", count=len(orders)) + "\n" + "─" * 25 + "\n\n"
        for i, order in enumerate(orders[:10]):
            status = STATUS_EMOJI.get(order.get('status', ''), order.get('status', 'N/A'))
            ts = order.get('timestamp', 'N/A')
            if ts and len(ts) > 16:
                ts = ts[:16]
            message += (
                f"<b>#{i+1}</b> {escape_html(order.get('product_name', 'N/A'))}\n"
                f"💰 ${order.get('price', 0.0):.2f}  |  {status}\n"
                f"🎮 ID: <code>{escape_html(order.get('game_id', 'N/A'))}</code>\n"
                f"📅 {escape_html(ts)}\n"
                f"─────────────\n"
            )
        if len(orders) > 10:
            message += f"\n... و {len(orders)-10} طلبات أخرى أقدم."
    
    # أزرار الإجراءات لكل طلب
    action_kb = []
    if orders:
        for order in orders[:5]:
            pid = order.get('purchase_id','')
            row = []
            if order.get('status') in ('Shipped','shipped','completed'):
                row.append(InlineKeyboardButton(f"🔁 إعادة #{pid[:6]}", callback_data=f"reorder_{pid}"))
                row.append(InlineKeyboardButton(f"🧾 فاتورة", callback_data=f"invoice_{pid}"))
                row.append(InlineKeyboardButton(f"💸 استرداد", callback_data=f"refund_select_{pid}"))
            if row:
                action_kb.append(row)
    action_kb.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")])
    markup = InlineKeyboardMarkup(action_kb)
    if update.message:
        await update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=markup)
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
    
    # فحص وجود عرض نشط على المنتج
    flash = await get_flash_offer_by_product_db(product_id)
    final_price = flash['discounted_price'] if flash else product['price']
    context.user_data['purchase_product_id'] = product_id
    context.user_data['purchase_product_name'] = product['name']
    context.user_data['purchase_price'] = final_price
    context.user_data['flash_offer'] = flash
    
    user_id = update.effective_user.id
    
    # سؤال الكوبون أولاً
    user_id = update.effective_user.id
    price_line = await get_price_line(user_id, product['price'])
    keyboard = [
        [InlineKeyboardButton("🎟️ لدي كوبون خصم", callback_data="apply_coupon")],
        [InlineKeyboardButton("⏩ تخطي", callback_data="skip_coupon")],
    ]
    flash_line = ""
    if flash:
        from datetime import datetime
        expires = datetime.strptime(flash['expires_at'], '%Y-%m-%d %H:%M:%S')
        remaining = expires - datetime.now()
        hours = int(remaining.total_seconds() // 3600)
        mins  = int((remaining.total_seconds() % 3600) // 60)
        flash_line = f"\n🔥 <b>عرض محدود!</b> ينتهي خلال {hours}س {mins}د"
    await query.message.reply_text(
        f"🛒 <b>{escape_html(product['name'])}</b>\n"
        f"💰 السعر: {price_line}{flash_line}\n\n"
        "هل لديك كوبون خصم؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return ASK_COUPON

async def handle_saved_game_id_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة اختيار معرف لعبة محفوظ."""
    query = update.callback_query
    
    if query.data == "enter_new_game_id":
        await query.message.reply_text(
            "🎮 يرجى إرسال معرف اللعبة الجديد:\n\nلإلغاء العملية، أرسل /cancel"
        )
        return ASK_GAME_ID
    elif query.data == "cancel_purchase":
        lang = await get_user_language_db(update.effective_user.id)
        await query.message.reply_text(t(lang,"purchase_cancelled"))
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

    # فحص 2FA قبل الشراء
    needs_2fa = await check_2fa_and_purchase(update, context, game_id)
    if needs_2fa:
        return ConversationHandler.END
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
    lang = await get_user_language_db(user_id)
    user_wallet = await get_user_wallet(user_id)
    if user_wallet < price:
        error_msg = t(lang,'wallet_insufficient', price=f"${price:.2f}", balance=f"${user_wallet:.2f}")
        if is_callback:
            await update.callback_query.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return

    new_balance = user_wallet - price
    await update_user_wallet(user_id, new_balance, username)

    # مكافأة المُحيل عند أول شراء
    referrer_id = await get_referrer_db(user_id)
    if referrer_id:
        reward = await get_referral_reward_db()
        referrer_balance = await get_user_wallet(referrer_id)
        await update_user_wallet(referrer_id, referrer_balance + reward)
        await mark_referral_rewarded_db(user_id)
        try:
            ref_lang = await get_user_language_db(referrer_id)
            await context.bot.send_message(
                chat_id=referrer_id,
                text=t(ref_lang,'referral_reward_msg', reward=f"${reward:.2f}"),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f'Failed to notify referrer: {e}')

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
    coupon_code = context.user_data.get('coupon_code')
    discount = context.user_data.get('discount', 0)
    coupon_line = f"\n🎟️ كوبون: <code>{escape_html(coupon_code)}</code> (وفّرت ${discount:.2f})" if coupon_code else ""
    if coupon_code:
        await use_coupon_db(coupon_code)
    price_line = await get_price_line(user_id, price)
    bal_line   = await format_price(user_id, new_balance)
    confirmation_message = t(lang,'purchase_success',
        product=escape_html(product_name),
        game_id=escape_html(game_id),
        price=price_line,
        balance=bal_line
    ) + coupon_line + "\n\n⏳ " + ("سيتم تنفيذ الطلب قريباً وستصلك رسالة عند الشحن." if lang=='ar' else "Your order will be processed soon." if lang=='en' else "داواکارییەکەت بەم زووانە جێبەجێ دەکرێت.")
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
    lang = await get_user_language_db(user_id)
    user_wallet = await get_user_wallet(user_id)
    
    keyboard = []
    for method_key, method_data in PAYMENT_METHODS.items():
        if method_data.get('enabled', False):
            keyboard.append([InlineKeyboardButton(
                method_data['name'], 
                callback_data=f"deposit_{method_key}"
            )])
    keyboard.append([InlineKeyboardButton(t(lang,"back"), callback_data="main_menu")])
    currency = await get_user_currency_db(user_id)
    rate = await get_exchange_rate_db()
    if currency == 'SYP':
        balance_display = f"{user_wallet * rate:,.0f} ل.س  (${user_wallet:.2f})"
    else:
        balance_display = f"${user_wallet:.2f}"
    message = f"{t(lang,'wallet_title')}\n\n{t(lang,'wallet_balance', balance=escape_html(balance_display))}\n\n{t(lang,'wallet_choose_method')}"
    
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
    lang = await get_user_language_db(update.effective_user.id)
    sham_code = PAYMENT_METHODS.get('sham_cash', {}).get('code', 'b441bd2368ed511aebd2f9e79723936d')
    message = (
        f"{t(lang,'sham_cash_title')}\n\n"
        f"{t(lang,'sham_cash_steps', code=escape_html(sham_code))}\n\n"
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
        lang = await get_user_language_db(update.effective_user.id)
        await update.message.reply_text(t(lang,"admin_only"))
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
        lang = await get_user_language_db(update.effective_user.id)
        await update.message.reply_text(t(lang,"admin_only"))
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
    """عرض الإحصائيات الشاملة."""
    if update.effective_user.id != ADMIN_USER_ID:
        if update.message:
            lang = await get_user_language_db(update.effective_user.id)
        await update.message.reply_text(t(lang,"admin_only"))
        return

    total_users    = await get_total_users_db()
    new_today      = await get_new_users_today_db()
    active_24h     = await get_active_users_last_24_hours_db()
    total_orders   = await get_total_orders_db()
    total_revenue  = await get_total_revenue_db()
    today_revenue  = await get_revenue_today_db()
    top_products   = await get_top_products_db(5)
    pending_orders = await get_pending_orders_db()
    pending_deps   = await get_pending_deposits_db()

    top_text = ""
    for i, p in enumerate(top_products, 1):
        top_text += f"  {i}. {escape_html(p['product_name'])} — {p['count']} مبيع (${ p['revenue']:.2f})\n"

    msg = (
        "📊 <b>إحصائيات المتجر</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👥 <b>المستخدمون</b>\n"
        f"  • الإجمالي: <b>{total_users}</b>\n"
        f"  • جدد اليوم: <b>{new_today}</b>\n"
        f"  • نشطون (24س): <b>{active_24h}</b>\n\n"
        "💰 <b>الإيرادات</b>\n"
        f"  • اليوم: <b>${today_revenue:.2f}</b>\n"
        f"  • الإجمالي: <b>${total_revenue:.2f}</b>\n"
        f"  • عدد الطلبات: <b>{total_orders}</b>\n\n"
        "⏳ <b>المعلق</b>\n"
        f"  • طلبات شحن معلقة: <b>{len(pending_orders)}</b>\n"
        f"  • طلبات إيداع معلقة: <b>{len(pending_deps)}</b>\n"
    )
    if top_text:
        msg += f"\n🏆 <b>أكثر المنتجات مبيعاً</b>\n{top_text}"

    keyboard = [
        [InlineKeyboardButton("⏳ الطلبات المعلقة", callback_data="admin_pending_orders")],
        [InlineKeyboardButton("💳 الإيداعات المعلقة", callback_data="admin_pending_deposits")],
        [InlineKeyboardButton("👤 بحث عن مستخدم", callback_data="admin_search_user")],
    ]
    if update.message:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_pending_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض الطلبات المعلقة مع أزرار تأكيد."""
    if update.effective_user.id != ADMIN_USER_ID:
        return
    orders = await get_pending_orders_db()
    if not orders:
        await update.callback_query.answer("✅ لا توجد طلبات معلقة!", show_alert=True)
        return
    for o in orders[:10]:
        msg = (
            f"🛒 <b>طلب معلق</b>\n"
            f"👤 {escape_html(o['username'])} (ID: {o['user_id']})\n"
            f"📦 {escape_html(o['product_name'])}\n"
            f"🎮 معرف: <code>{escape_html(o['game_id'])}</code>\n"
            f"💰 ${o['price']:.2f}\n"
            f"📅 {str(o['timestamp'])[:16]}"
        )
        keyboard = [[InlineKeyboardButton(
            "✅ تأكيد الشحن",
            callback_data=f"confirm_ship_{o['purchase_id']}"
        )]]
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.callback_query.answer()


async def admin_pending_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض طلبات الإيداع المعلقة مع أزرار تأكيد."""
    if update.effective_user.id != ADMIN_USER_ID:
        return
    deposits = await get_pending_deposits_db()
    if not deposits:
        await update.callback_query.answer("✅ لا توجد إيداعات معلقة!", show_alert=True)
        return
    for d in deposits[:10]:
        msg = (
            f"💳 <b>إيداع معلق</b>\n"
            f"👤 {escape_html(d['username'])} (ID: {d['user_id']})\n"
            f"💰 المبلغ: <b>${d['amount']:.2f}</b>\n"
            f"🏦 الطريقة: {escape_html(d['payment_method'])}\n"
            f"🔢 رقم العملية: <code>{escape_html(d['transaction_id'])}</code>\n"
            f"📅 {str(d['timestamp'])[:16]}"
        )
        keyboard = [[InlineKeyboardButton(
            f"✅ تأكيد إضافة ${d['amount']:.2f}",
            callback_data=f"confirm_dep_{d['user_id']}_{d['amount']}_{d['payment_id']}"
        )]]
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.callback_query.answer()


async def admin_confirm_ship_btn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تأكيد شحن طلب عبر الزر."""
    if update.effective_user.id != ADMIN_USER_ID:
        return
    purchase_id = update.callback_query.data.replace("confirm_ship_", "")
    purchase = await get_purchase_by_id_db(purchase_id)
    if not purchase:
        await update.callback_query.answer("❌ الطلب غير موجود.", show_alert=True)
        return
    shipped_at = datetime.now().isoformat()
    await update_purchase_status_db(purchase_id, "Shipped", shipped_at)
    try:
        await context.bot.send_message(
            chat_id=purchase['user_id'],
            text=(
                f"✅ <b>تم شحن طلبك!</b>\n\n"
                f"📦 المنتج: {escape_html(purchase.get('product_name',''))}\n"
                f"🎮 المعرف: <code>{escape_html(purchase.get('game_id',''))}</code>\n\n"
                f"شكراً لتسوقك معنا! 🙏"
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to notify user: {e}")
    await update.callback_query.edit_message_reply_markup(reply_markup=None)
    await update.callback_query.answer("✅ تم تأكيد الشحن وإشعار المستخدم!", show_alert=True)


async def admin_confirm_dep_btn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تأكيد إيداع عبر الزر."""
    if update.effective_user.id != ADMIN_USER_ID:
        return
    parts = update.callback_query.data.replace("confirm_dep_", "").split("_")
    user_id = int(parts[0])
    amount  = float(parts[1])
    pay_id  = "_".join(parts[2:])
    current = await get_user_wallet_db(user_id)
    await update_user_wallet_db(user_id, current + amount)
    # تحديث حالة الإيداع
    import sqlite3 as _sq
    from config import DATABASE_NAME as _DB
    conn = _sq.connect(_DB)
    conn.execute("UPDATE pending_payments SET status='confirmed' WHERE payment_id=?", (pay_id,))
    conn.commit(); conn.close()
    try:
        new_bal = await get_user_wallet_db(user_id)
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ <b>تم تأكيد إيداعك!</b>\n\n"
                f"💰 المبلغ المضاف: <b>${amount:.2f}</b>\n"
                f"👛 رصيدك الحالي: <b>${new_bal:.2f}</b>"
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to notify user: {e}")
    await update.callback_query.edit_message_reply_markup(reply_markup=None)
    await update.callback_query.answer(f"✅ تم إضافة ${amount:.2f} للمستخدم {user_id}!", show_alert=True)


async def admin_search_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بدء البحث عن مستخدم."""
    if update.effective_user.id != ADMIN_USER_ID:
        return
    await update.callback_query.edit_message_text(
        "👤 أرسل <b>ID المستخدم</b> للبحث عنه:",
        parse_mode=ParseMode.HTML
    )
    await update.callback_query.answer()
    context.user_data['admin_action'] = 'search_user'


async def admin_set_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء تعديل رصيد مستخدم."""
    if update.effective_user.id != ADMIN_USER_ID:
        return ConversationHandler.END
    await update.callback_query.edit_message_text(
        "💰 أرسل <b>ID المستخدم</b> لتعديل رصيده:",
        parse_mode=ParseMode.HTML
    )
    await update.callback_query.answer()
    return ADMIN_SET_BALANCE_USER


async def admin_set_balance_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        uid = int(update.message.text.strip())
        user = await get_user_info_db(uid)
        if not user:
            await update.message.reply_text("❌ المستخدم غير موجود.")
            return ADMIN_SET_BALANCE_USER
        context.user_data['target_user_id'] = uid
        await update.message.reply_text(
            f"👤 المستخدم: {escape_html(user.get('username','غير معروف'))}\n"
            f"💰 الرصيد الحالي: <b>${user.get('balance',0):.2f}</b>\n\n"
            f"أرسل الرصيد الجديد:",
            parse_mode=ParseMode.HTML
        )
        return ADMIN_SET_BALANCE_AMOUNT
    except ValueError:
        await update.message.reply_text("❌ أرسل رقم ID صحيح.")
        return ADMIN_SET_BALANCE_USER


async def admin_set_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        new_bal = float(update.message.text.strip())
        if new_bal < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ أدخل رقماً صحيحاً >= 0.")
        return ADMIN_SET_BALANCE_AMOUNT
    uid = context.user_data.get('target_user_id')
    await set_user_balance_db(uid, new_bal)
    try:
        await context.bot.send_message(
            chat_id=uid,
            text=f"💰 تم تحديث رصيد محفظتك إلى <b>${new_bal:.2f}</b>",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass
    await update.message.reply_text(f"✅ تم تعيين رصيد المستخدم {uid} إلى ${new_bal:.2f}")
    context.user_data.clear()
    return ConversationHandler.END

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية البث."""
    if update.effective_user.id != ADMIN_USER_ID:
        lang = await get_user_language_db(update.effective_user.id)
        await update.message.reply_text(t(lang,"admin_only"))
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
        lang = await get_user_language_db(update.effective_user.id)
        await update.message.reply_text(t(lang,"admin_only"))
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

    # معالجة رابط الإحالة
    if context.args and context.args[0].startswith('ref_'):
        try:
            referrer_id = int(context.args[0].replace('ref_', ''))
            if referrer_id != user_id:
                added = await add_referral_db(referrer_id, user_id)
                if added:
                    logger.info(f'New referral: {user_id} referred by {referrer_id}')
        except (ValueError, Exception) as e:
            logger.error(f'Referral error: {e}')

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

    lang = await get_user_language_db(user_id)
    message = f"مرحباً بك في <b>{escape_html(WEBSITE_NAME)}</b>!\n\n{escape_html(WEBSITE_SLOGAN)}"

    if update.message:
        await update.message.reply_text(
            message,
            reply_markup=get_main_menu_keyboard(lang),
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
    elif text == "⚙️ إعداداتي":
        await show_settings(update, context)
    elif text == "🔗 إحالة صديق":
        await show_referral(update, context)
    elif text == "⚡ العروض":
        await show_flash_offers(update, context)
    elif text == "ℹ️ معلومات عنا":
        await show_about_us(update, context)
    elif text == "💬 دعم العملاء":
        await support_menu(update, context)
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

# --- دوال الكوبونات ---


# --- إعدادات الحساب والعملة ---

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض صفحة إعدادات الحساب."""
    user_id  = update.effective_user.id
    username = update.effective_user.first_name or update.effective_user.username or "مستخدم"
    lang     = await get_user_language_db(user_id)
    currency = await get_user_currency_db(user_id)
    balance  = await get_user_wallet(user_id)
    rate     = await get_exchange_rate_db()
    two_fa   = await get_user_2fa_db(user_id)

    currency_flag = t(lang,'currency_usd') if currency == "USD" else t(lang,'currency_syp')
    balance_usd   = f"${balance:.2f}"
    balance_syp   = f"{balance * rate:,.0f} ل.س"
    balance_line  = balance_usd if currency == "USD" else f"{balance_syp} ({balance_usd})"
    fa_status     = t(lang,'2fa_on') if two_fa else t(lang,'2fa_off')
    two_fa_btn    = t(lang,'disable_2fa') if two_fa else t(lang,'enable_2fa')

    msg = (
        f"{t(lang,'settings_title')}\n\n"
        f"{t(lang,'settings_name', name=escape_html(username))}\n"
        f"{t(lang,'settings_balance', balance=balance_line)}\n"
        f"{t(lang,'settings_currency', currency=currency_flag)}\n"
        f"{t(lang,'settings_rate', rate=f"{rate:,.0f}")}\n"
        f"{t(lang,'settings_2fa', status=fa_status)}\n"
    )
    keyboard = [
        [
            InlineKeyboardButton(t(lang,'currency_usd'), callback_data="set_currency_USD"),
            InlineKeyboardButton(t(lang,'currency_syp'), callback_data="set_currency_SYP"),
        ],
        [InlineKeyboardButton(t(lang,'change_language'), callback_data="show_language")],
        [InlineKeyboardButton(two_fa_btn, callback_data="toggle_2fa")],
        [InlineKeyboardButton(t(lang,'back'), callback_data="main_menu")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)
        except BadRequest:
            await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=markup)


async def handle_set_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة اختيار العملة."""
    query  = update.callback_query
    currency = query.data.replace("set_currency_", "")
    user_id  = update.effective_user.id

    await set_user_currency_db(user_id, currency)

    lang = await get_user_language_db(user_id)
    flag = t(lang,'currency_usd') if currency == "USD" else t(lang,'currency_syp')
    await query.answer(f"✅ {flag}", show_alert=True)
    await show_settings(update, context)


# --- أدمن: تحديث سعر الصرف ---

async def admin_set_rate_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء تحديث سعر الصرف."""
    if update.effective_user.id != ADMIN_USER_ID:
        return ConversationHandler.END
    rate = await get_exchange_rate_db()
    msg = "💱 <b>تحديث سعر الصرف</b>\n\n" + f"السعر الحالي: <b>1$ = {rate:,.0f} ل.س</b>\n\n" + "أرسل السعر الجديد (مثال: 14000):"
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    return ADMIN_SET_RATE

async def admin_set_rate_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال سعر الصرف الجديد."""
    try:
        rate = float(update.message.text.strip().replace(",", ""))
        if rate <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ أدخل رقماً صحيحاً أكبر من الصفر.")
        return ADMIN_SET_RATE

    await set_exchange_rate_db(rate)
    msg = "✅ <b>تم تحديث سعر الصرف!</b>\n\n" + f"💱 1 دولار = <b>{rate:,.0f} ليرة سورية</b>"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    context.user_data.clear()
    return ConversationHandler.END



# --- نظام الإحالة ---

async def show_referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض رابط الإحالة وإحصائياته."""
    user_id = update.effective_user.id
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    stats = await get_referral_stats_db(user_id)
    reward = await get_referral_reward_db()

    msg = (
        "🔗 <b>نظام الإحالة</b>\n\n"
        f"شارك رابطك الخاص مع أصدقائك.\n"
        f"عند أول شراء لكل صديق تدعوه تحصل على <b>${reward:.2f}</b>!\n\n"
        f"🔗 رابطك الخاص:\n<code>{ref_link}</code>\n\n"
        f"📊 <b>إحصائياتك:</b>\n"
        f"👥 عدد الأصدقاء المدعوين: <b>{stats['total']}</b>\n"
        f"💰 مكافآت محصّلة: <b>{stats['paid']}</b> (${ stats['paid'] * reward:.2f})"
    )
    keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")]]
    if update.message:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))


# --- العروض المحدودة ---

async def show_flash_offers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض العروض النشطة للمستخدمين."""
    from datetime import datetime
    offers = await get_active_flash_offers_db()
    if not offers:
        msg = "⚡ <b>العروض المحدودة</b>\n\nلا توجد عروض نشطة حالياً.\nتابع البوت لتعرف عن العروض القادمة!"
    else:
        lang = await get_user_language_db(update.effective_user.id)
        msg = t(lang,"offers_title") + "\n\n"
        for o in offers:
            product = await get_product_by_id_db(o['product_id'])
            name = product['name'] if product else o['product_id']
            expires = datetime.strptime(o['expires_at'], '%Y-%m-%d %H:%M:%S')
            remaining = expires - datetime.now()
            hours = int(remaining.total_seconds() // 3600)
            mins  = int((remaining.total_seconds() % 3600) // 60)
            discount_pct = int((1 - o['discounted_price'] / o['original_price']) * 100)
            msg += (
                f"🔥 <b>{escape_html(name)}</b>\n"
                f"💰 <s>${o['original_price']:.2f}</s> ← <b>${o['discounted_price']:.2f}</b> (-{discount_pct}%)\n"
                f"⏰ ينتهي خلال: <b>{hours}س {mins}د</b>\n\n"
            )
    keyboard = [[InlineKeyboardButton("🎮 تسوق الآن", callback_data="show_games")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")]]
    if update.message:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))


# --- أدمن: إدارة العروض ---

async def admin_flash_offers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """لوحة إدارة العروض للأدمن."""
    if update.effective_user.id != ADMIN_USER_ID:
        return
    from datetime import datetime
    offers = await get_active_flash_offers_db()
    msg = "⚡ <b>العروض المحدودة النشطة</b>\n\n"
    if offers:
        for o in offers:
            product = await get_product_by_id_db(o['product_id'])
            name = product['name'] if product else o['product_id']
            expires = datetime.strptime(o['expires_at'], '%Y-%m-%d %H:%M:%S')
            remaining = expires - datetime.now()
            hours = int(remaining.total_seconds() // 3600)
            msg += f"• {escape_html(name)} — ${o['discounted_price']:.2f} | {hours}س متبقي (ID:{o['id']})\n"
    else:
        msg += "لا توجد عروض نشطة."
    keyboard = [
        [InlineKeyboardButton("➕ إضافة عرض", callback_data="admin_add_offer")],
        [InlineKeyboardButton("❌ إلغاء عرض", callback_data="admin_cancel_offer")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")],
    ]
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        await update.callback_query.answer()
    else:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_add_offer_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء إضافة عرض."""
    await update.callback_query.edit_message_text(
        "➕ <b>إضافة عرض محدود</b>\n\nأرسل <b>معرف المنتج</b> (product_id):\nمثال: 100 أو pubg_60",
        parse_mode=ParseMode.HTML
    )
    await update.callback_query.answer()
    return ADD_OFFER_PRODUCT


async def admin_add_offer_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    product_id = update.message.text.strip()
    product = await get_product_by_id_db(product_id)
    if not product:
        await update.message.reply_text("❌ المنتج غير موجود. أرسل معرفاً صحيحاً:")
        return ADD_OFFER_PRODUCT
    context.user_data['offer_product_id'] = product_id
    context.user_data['offer_original_price'] = product['price']
    await update.message.reply_text(
        f"✅ المنتج: <b>{escape_html(product['name'])}</b>\n"
        f"السعر الأصلي: <b>${product['price']:.2f}</b>\n\n"
        f"أرسل <b>السعر الجديد المخفض</b>:",
        parse_mode=ParseMode.HTML
    )
    return ADD_OFFER_PRICE


async def admin_add_offer_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.strip())
        original = context.user_data.get('offer_original_price', 0)
        if price <= 0 or price >= original:
            await update.message.reply_text(f"❌ السعر يجب أن يكون أقل من ${original:.2f} وأكبر من 0.")
            return ADD_OFFER_PRICE
        context.user_data['offer_price'] = price
    except ValueError:
        await update.message.reply_text("❌ أدخل رقماً صحيحاً.")
        return ADD_OFFER_PRICE
    await update.message.reply_text("⏰ كم ساعة يستمر العرض؟ (مثال: 2 أو 24):")
    return ADD_OFFER_HOURS


async def admin_add_offer_hours(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from datetime import datetime, timedelta
    try:
        hours = float(update.message.text.strip())
        if hours <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ أدخل عدد ساعات صحيح.")
        return ADD_OFFER_HOURS

    product_id    = context.user_data['offer_product_id']
    discounted    = context.user_data['offer_price']
    original      = context.user_data['offer_original_price']
    expires_at    = (datetime.now() + timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
    discount_pct  = int((1 - discounted / original) * 100)

    offer_id = await add_flash_offer_db(product_id, discounted, original, expires_at)

    product = await get_product_by_id_db(product_id)
    name = product['name'] if product else product_id

    await update.message.reply_text(
        f"✅ <b>تم إضافة العرض!</b>\n\n"
        f"📦 المنتج: {escape_html(name)}\n"
        f"💰 <s>${original:.2f}</s> ← <b>${discounted:.2f}</b> (-{discount_pct}%)\n"
        f"⏰ ينتهي بعد: {hours} ساعة\n\n"
        f"سيظهر العرض تلقائياً عند شراء هذا المنتج 🔥",
        parse_mode=ParseMode.HTML
    )
    # نشر في القناة تلقائياً
    await publish_flash_offer_to_channel(context, name, original, discounted, hours, product_id)
    context.user_data.clear()
    return ConversationHandler.END


async def admin_cancel_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إلغاء عرض نشط."""
    if update.effective_user.id != ADMIN_USER_ID:
        return
    offers = await get_active_flash_offers_db()
    if not offers:
        await update.callback_query.answer("لا توجد عروض نشطة.", show_alert=True)
        return
    keyboard = []
    for o in offers:
        product = await get_product_by_id_db(o['product_id'])
        name = product['name'] if product else o['product_id']
        keyboard.append([InlineKeyboardButton(f"❌ {name[:30]}", callback_data=f"del_offer_{o['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_flash_offers")])
    await update.callback_query.edit_message_text(
        "اختر العرض للإلغاء:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await update.callback_query.answer()


async def admin_del_offer_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    offer_id = int(update.callback_query.data.replace("del_offer_", ""))
    # جلب اسم المنتج قبل الإلغاء
    offers = await get_active_flash_offers_db()
    offer = next((o for o in offers if o['id'] == offer_id), None)
    await deactivate_flash_offer_db(offer_id)
    if offer:
        product = await get_product_by_id_db(offer['product_id'])
        name = product['name'] if product else offer['product_id']
        await publish_offer_ended_to_channel(context, name)
    await update.callback_query.answer("✅ تم إلغاء العرض.", show_alert=True)
    await admin_flash_offers(update, context)


# --- أدمن: تعديل مكافأة الإحالة ---

async def admin_set_ref_reward_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_USER_ID:
        return ConversationHandler.END
    reward = await get_referral_reward_db()
    await update.callback_query.edit_message_text(
        f"🎁 المكافأة الحالية: <b>${reward:.2f}</b>\n\nأرسل المكافأة الجديدة:",
        parse_mode=ParseMode.HTML
    )
    await update.callback_query.answer()
    return ADMIN_SET_REF_REWARD


async def admin_set_ref_reward_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = float(update.message.text.strip())
        if amount < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ أدخل رقماً صحيحاً >= 0.")
        return ADMIN_SET_REF_REWARD
    await set_referral_reward_db(amount)
    await update.message.reply_text(f"✅ تم تحديث مكافأة الإحالة إلى <b>${amount:.2f}</b>", parse_mode=ParseMode.HTML)
    return ConversationHandler.END




# --- دعم العملاء ---

async def support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """قائمة دعم العملاء."""
    user_id = update.effective_user.id
    lang = await get_user_language_db(user_id)
    tickets = await get_user_tickets_db(user_id)
    open_count = sum(1 for tk in tickets if tk['status'] != 'closed')

    msg = (
        f"{t(lang,'support_title')}\n\n"
        f"{t(lang,'support_desc')}\n\n"
        f"{t(lang,'support_stats', total=len(tickets), open=open_count)}"
    )
    keyboard = [
        [InlineKeyboardButton(t(lang,'new_ticket'), callback_data="support_new")],
    ]
    if tickets:
        keyboard.append([InlineKeyboardButton(t(lang,'my_tickets'), callback_data="support_my_tickets")])
    keyboard.append([InlineKeyboardButton(t(lang,'back'), callback_data="main_menu")])

    if update.message:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))


async def support_new_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء تذكرة جديدة."""
    lang = await get_user_language_db(update.effective_user.id)
    await update.callback_query.edit_message_text(t(lang,'ticket_subject_ask'), parse_mode=ParseMode.HTML)
    await update.callback_query.answer()
    return SUPPORT_SUBJECT


async def support_receive_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال موضوع التذكرة."""
    subject = update.message.text.strip()
    lang = await get_user_language_db(update.effective_user.id)
    if len(subject) < 3:
        await update.message.reply_text(t(lang,'ticket_subject_short'))
        return SUPPORT_SUBJECT
    context.user_data['ticket_subject'] = subject
    await update.message.reply_text(t(lang,'ticket_msg_ask', subject=escape_html(subject)), parse_mode=ParseMode.HTML)
    return SUPPORT_MESSAGE


async def support_receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال رسالة التذكرة وإنشاؤها."""
    message = update.message.text.strip()
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    subject = context.user_data.get('ticket_subject', 'بدون موضوع')

    ticket_id = await create_ticket_db(user_id, username, subject)
    await add_ticket_message_db(ticket_id, 'user', message)

    # إشعار الأدمن
    try:
        admin_msg = (
            f"🎫 <b>تذكرة جديدة #{ticket_id}</b>\n\n"
            f"👤 {escape_html(username)} (ID: {user_id})\n"
            f"📌 الموضوع: {escape_html(subject)}\n"
            f"💬 الرسالة: {escape_html(message[:200])}"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"↩️ رد على التذكرة #{ticket_id}", callback_data=f"admin_reply_{ticket_id}")
        ]])
        await context.bot.send_message(chat_id=ADMIN_USER_ID, text=admin_msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Failed to notify admin about ticket: {e}")

    lang = await get_user_language_db(user_id)
    await update.message.reply_text(t(lang,'ticket_created', id=ticket_id), parse_mode=ParseMode.HTML)
    context.user_data.clear()
    return ConversationHandler.END


async def support_my_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض تذاكر المستخدم."""
    user_id = update.effective_user.id
    tickets = await get_user_tickets_db(user_id)

    if not tickets:
        await update.callback_query.answer("لا توجد تذاكر.", show_alert=True)
        return

    STATUS = {'open': '🟢 مفتوحة', 'closed': '🔴 مغلقة', 'answered': '🔵 مجاب عليها'}
    msg = "📋 <b>تذاكري</b>\n\n"
    keyboard = []
    for t in tickets[:8]:
        status = STATUS.get(t['status'], t['status'])
        msg += f"#{t['id']} — {escape_html(t['subject'][:30])} | {status}\n"
        keyboard.append([InlineKeyboardButton(
            f"#{t['id']} {t['subject'][:25]}",
            callback_data=f"support_view_{t['id']}"
        )])
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="support_menu")])

    try:
        await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    except BadRequest:
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.callback_query.answer()


async def support_view_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض محادثة تذكرة."""
    ticket_id = int(update.callback_query.data.replace("support_view_", ""))
    ticket = await get_ticket_by_id_db(ticket_id)
    messages = await get_ticket_messages_db(ticket_id)

    if not ticket:
        await update.callback_query.answer("❌ التذكرة غير موجودة.", show_alert=True)
        return

    STATUS = {'open': '🟢 مفتوحة', 'closed': '🔴 مغلقة', 'answered': '🔵 مجاب عليها'}
    msg = (
        f"🎫 <b>تذكرة #{ticket_id}</b>\n"
        f"📌 {escape_html(ticket['subject'])}\n"
        f"الحالة: {STATUS.get(ticket['status'], ticket['status'])}\n"
        f"─────────────────\n\n"
    )
    for m in messages:
        sender = "أنت 👤" if m['sender'] == 'user' else "الدعم 🛡️"
        time = str(m['sent_at'])[:16]
        msg += f"<b>{sender}</b> [{time}]:\n{escape_html(m['message'])}\n\n"

    keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="support_my_tickets")]]
    try:
        await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    except BadRequest:
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.callback_query.answer()


# --- دعم العملاء للأدمن ---

async def admin_support_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """لوحة تذاكر الدعم للأدمن."""
    if update.effective_user.id != ADMIN_USER_ID:
        return
    tickets = await get_open_tickets_db()
    msg = f"🎫 <b>تذاكر الدعم المفتوحة</b> ({len(tickets)})\n\n"
    keyboard = []
    if tickets:
        for t in tickets[:10]:
            msg += f"#{t['id']} — {escape_html(t['username'] or 'مجهول')} | {escape_html(t['subject'][:25])}\n"
            keyboard.append([InlineKeyboardButton(
                f"#{t['id']} {t['subject'][:20]} — {t['username'] or 'مجهول'}",
                callback_data=f"admin_ticket_{t['id']}"
            )])
    else:
        msg += "لا توجد تذاكر مفتوحة ✅"
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_panel")])

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        await update.callback_query.answer()
    else:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_view_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض تذكرة للأدمن مع خيار الرد والإغلاق."""
    ticket_id = int(update.callback_query.data.replace("admin_ticket_", ""))
    ticket = await get_ticket_by_id_db(ticket_id)
    messages = await get_ticket_messages_db(ticket_id)

    msg = (
        f"🎫 <b>تذكرة #{ticket_id}</b>\n"
        f"👤 {escape_html(ticket.get('username','مجهول'))} (ID: {ticket['user_id']})\n"
        f"📌 {escape_html(ticket['subject'])}\n"
        f"─────────────────\n\n"
    )
    for m in messages:
        sender = "المستخدم 👤" if m['sender'] == 'user' else "الدعم 🛡️"
        time = str(m['sent_at'])[:16]
        msg += f"<b>{sender}</b> [{time}]:\n{escape_html(m['message'])}\n\n"

    keyboard = [
        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_{ticket_id}"),
         InlineKeyboardButton("✅ إغلاق", callback_data=f"admin_close_{ticket_id}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_support")]
    ]
    try:
        await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    except BadRequest:
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.callback_query.answer()


async def admin_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء الرد على تذكرة."""
    ticket_id = int(update.callback_query.data.replace("admin_reply_", ""))
    context.user_data['reply_ticket_id'] = ticket_id
    await update.callback_query.edit_message_text(
        f"↩️ <b>رد على التذكرة #{ticket_id}</b>\n\nأرسل ردك:\n\nلإلغاء: /cancel",
        parse_mode=ParseMode.HTML
    )
    await update.callback_query.answer()
    return SUPPORT_REPLY


async def admin_reply_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إرسال رد الأدمن."""
    ticket_id = context.user_data.get('reply_ticket_id')
    reply = update.message.text.strip()
    ticket = await get_ticket_by_id_db(ticket_id)

    if not ticket:
        await update.message.reply_text("❌ التذكرة غير موجودة.")
        return ConversationHandler.END

    await add_ticket_message_db(ticket_id, 'admin', reply)

    # إشعار المستخدم
    try:
        user_lang = await get_user_language_db(ticket['user_id'])
        await context.bot.send_message(
            chat_id=ticket['user_id'],
            text=t(user_lang,'ticket_reply', id=ticket_id, subject=escape_html(ticket['subject']), reply=escape_html(reply)),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to notify user about ticket reply: {e}")

    await update.message.reply_text(f"✅ تم إرسال الرد على التذكرة #{ticket_id}!")
    context.user_data.clear()
    return ConversationHandler.END


async def admin_close_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إغلاق تذكرة."""
    ticket_id = int(update.callback_query.data.replace("admin_close_", ""))
    ticket = await get_ticket_by_id_db(ticket_id)
    await close_ticket_db(ticket_id)

    try:
        user_lang = await get_user_language_db(ticket['user_id'])
        await context.bot.send_message(
            chat_id=ticket['user_id'],
            text=t(user_lang,'ticket_closed_msg', id=ticket_id),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    await update.callback_query.answer(f"✅ تم إغلاق التذكرة #{ticket_id}", show_alert=True)
    await admin_support_panel(update, context)



# ==========================================
# نظام الاسترداد
# ==========================================

async def show_refund_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض طلبات قابلة للاسترداد."""
    user_id = update.effective_user.id
    lang = await get_user_language_db(user_id)
    purchases = await get_user_purchases_history_db(user_id)
    eligible = [p for p in purchases if p['status'] in ('Shipped', 'shipped', 'completed')][:5]

    if not eligible:
        msg = t(lang,'refund_no_orders')
        kb = [[InlineKeyboardButton(t(lang,'back'), callback_data="main_menu")]]
        if update.callback_query:
            await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            await update.callback_query.answer()
        return

    msg = f"{t(lang,'refund_title')}\n\n{t(lang,'refund_select')}"
    kb = []
    for p in eligible:
        kb.append([InlineKeyboardButton(
            f"#{p['purchase_id'][:8]} — {p['product_name'][:20]} (${p['price']:.2f})",
            callback_data=f"refund_select_{p['purchase_id']}"
        )])
    kb.append([InlineKeyboardButton(t(lang,'back'), callback_data="show_orders_cb")])
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
        await update.callback_query.answer()


async def refund_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """اختيار طلب للاسترداد."""
    purchase_id = update.callback_query.data.replace("refund_select_", "")
    context.user_data['refund_purchase_id'] = purchase_id
    await update.callback_query.edit_message_text(
        "💸 <b>طلب استرداد</b>\n\nأرسل <b>سبب</b> طلب الاسترداد:\n\nلإلغاء: /cancel",
        parse_mode=ParseMode.HTML
    )
    await update.callback_query.answer()
    return REFUND_REASON


async def refund_receive_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال سبب الاسترداد."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    reason = update.message.text.strip()
    purchase_id = context.user_data.get('refund_purchase_id')

    success = await request_refund_db(purchase_id, user_id, reason)
    if not success:
        await update.message.reply_text("❌ فشل إرسال الطلب. حاول مجدداً.")
        return ConversationHandler.END

    # إشعار الأدمن
    try:
        purchase = await get_purchase_by_id_db(purchase_id)
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ قبول", callback_data=f"refund_approve_{purchase_id}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"refund_reject_{purchase_id}")
            ]
        ])
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=(
                f"💸 <b>طلب استرداد جديد</b>\n\n"
                f"👤 {escape_html(username)} (ID: {user_id})\n"
                f"📦 {escape_html(purchase.get('product_name',''))}\n"
                f"💰 ${purchase.get('price',0):.2f}\n"
                f"📝 السبب: {escape_html(reason)}"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Failed to notify admin about refund: {e}")

    lang = await get_user_language_db(user_id)
    await update.message.reply_text(t(lang,'refund_sent'), parse_mode=ParseMode.HTML)
    context.user_data.clear()
    return ConversationHandler.END


async def admin_process_refund(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الأدمن يقبل أو يرفض الاسترداد."""
    data = update.callback_query.data
    approve = data.startswith("refund_approve_")
    purchase_id = data.replace("refund_approve_", "").replace("refund_reject_", "")

    result = await process_refund_db(purchase_id, approve)
    if not result:
        await update.callback_query.answer("❌ الطلب غير موجود.", show_alert=True)
        return

    user_lang = await get_user_language_db(result['user_id'])
    if approve:
        msg_user  = t(user_lang,'refund_approved', amount=f"${result['price']:.2f}")
        msg_admin = f"✅ تم قبول استرداد ${result['price']:.2f} للمستخدم {result['user_id']}"
    else:
        msg_user  = t(user_lang,'refund_rejected')
        msg_admin = f"❌ تم رفض الاسترداد للمستخدم {result['user_id']}"

    try:
        await context.bot.send_message(chat_id=result['user_id'], text=msg_user, parse_mode=ParseMode.HTML)
    except Exception:
        pass

    await update.callback_query.edit_message_reply_markup(reply_markup=None)
    await update.callback_query.answer(msg_admin, show_alert=True)


# ==========================================
# اللغات
# ==========================================

async def show_language_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض إعدادات اللغة."""
    user_id = update.effective_user.id
    current_lang = await get_user_language_db(user_id)
    lang_labels = {'ar':'العربية','en':'English','ku':'کوردی'}
    msg = f"🌍 <b>{lang_labels.get(current_lang,'Language')}</b>\n\n{LANGUAGE_NAMES.get(current_lang,'')}"
    kb = [
        [InlineKeyboardButton(name, callback_data=f"set_lang_{code}")]
        for code, name in LANGUAGE_NAMES.items()
    ]
    kb.append([InlineKeyboardButton(t(current_lang,'back'), callback_data="user_settings")])
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
        await update.callback_query.answer()
    else:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))


async def handle_set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تغيير لغة المستخدم وتحديث أزرار القائمة."""
    lang = update.callback_query.data.replace("set_lang_", "")
    user_id = update.effective_user.id
    await set_user_language_db(user_id, lang)
    await update.callback_query.answer(t(lang, 'language_changed'), show_alert=True)
    # إرسال القائمة الجديدة بالأزرار بلغة المختارة
    await update.callback_query.message.reply_text(
        t(lang, 'welcome', name=WEBSITE_NAME),
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard(lang)
    )


# ==========================================
# التحقق بخطوتين
# ==========================================

async def toggle_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تفعيل/إيقاف التحقق بخطوتين."""
    user_id = update.effective_user.id
    lang = await get_user_language_db(user_id)
    current = await get_user_2fa_db(user_id)
    new_state = not current
    await set_user_2fa_db(user_id, new_state)
    if new_state:
        msg = t(lang, 'two_fa_enabled')
    else:
        msg = t(lang, 'two_fa_disabled')
    await update.callback_query.answer(msg, show_alert=True)
    await show_settings(update, context)


async def check_2fa_and_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str) -> bool:
    """فحص التحقق بخطوتين قبل الشراء. يعيد True إذا يجب الانتظار للتأكيد."""
    user_id = update.effective_user.id
    lang = await get_user_language_db(user_id)
    enabled = await get_user_2fa_db(user_id)
    price = context.user_data.get('purchase_price', 0)
    if not enabled or price < 2:
        return False

    product_name = context.user_data.get('purchase_product_name', '')
    price_line = await get_price_line(user_id, price)
    msg = t(lang,'confirm_purchase_msg',
        product=escape_html(product_name),
        price=price_line,
        game_id=escape_html(game_id)
    )
    context.user_data['pending_game_id_2fa'] = game_id
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t(lang,'confirm'), callback_data="confirm_2fa_purchase"),
            InlineKeyboardButton(t(lang,'cancel'), callback_data="cancel_purchase")
        ]
    ])
    if update.message:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=kb)
    return True


# ==========================================
# إعادة الطلب
# ==========================================

async def reorder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إعادة شراء نفس المنتج بنفس المعرف."""
    user_id = update.effective_user.id
    lang = await get_user_language_db(user_id)
    data = update.callback_query.data.replace("reorder_", "")
    purchase = await get_purchase_by_id_db(data)

    if not purchase:
        await update.callback_query.answer("❌ الطلب غير موجود.", show_alert=True)
        return

    product = await get_product_by_id_db(purchase['purchase_id'])
    flash = await get_flash_offer_by_product_db(str(purchase.get('product_id', '')))
    price = flash['discounted_price'] if flash else purchase['price']
    wallet = await get_user_wallet(user_id)

    if wallet < price:
        await update.callback_query.answer(t(lang,'wallet_insufficient', price=f"${price:.2f}", balance=f"${wallet:.2f}"), show_alert=True)
        return

    context.user_data['purchase_product_name'] = purchase['product_name']
    context.user_data['purchase_price'] = price
    context.user_data['discount'] = 0
    context.user_data['coupon_code'] = None
    context.user_data['flash_offer'] = flash

    needs_2fa = await check_2fa_and_purchase(update, context, purchase['game_id'])
    if not needs_2fa:
        await complete_purchase(update, context, purchase['game_id'], is_callback=True)
    await update.callback_query.answer()


# ==========================================
# تجميع الطلبات (Checkout)
# ==========================================

async def cart_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض ملخص السلة وتأكيد الشراء."""
    user_id = update.effective_user.id
    lang = await get_user_language_db(user_id)
    cart = await get_user_cart_db(user_id)

    if not cart:
        await update.callback_query.answer(t(lang,'cart_empty'), show_alert=True)
        return

    wallet = await get_user_wallet(user_id)
    total = sum(item['price'] for item in cart)

    if wallet < total:
        shortage = total - wallet
        await update.callback_query.answer(
            t(lang,'wallet_insufficient', price=f"${total:.2f}", balance=f"${wallet:.2f}"),
            show_alert=True
        )
        return

    total_line = await format_price(user_id, total)
    remain_line = await format_price(user_id, wallet - total)
    confirm_lbl = t(lang,'confirm') + " " + ("الكل" if lang=='ar' else "All" if lang=='en' else "هەموو")
    msg = f"🛒 <b>{t(lang,'confirm_purchase_title')}</b>\n\n"
    for item in cart:
        msg += f"• {escape_html(item['name'])} — ${item['price']:.2f}\n"
    msg += f"\n💰 <b>{t(lang,'cart_total')}: {total_line}</b>\n"
    msg += f"👛 " + ("رصيدك بعد الشراء" if lang=='ar' else "Balance after" if lang=='en' else "باڵانسی دوا") + f": <b>{remain_line}</b>\n\n"

    context.user_data['cart_checkout_items'] = cart
    context.user_data['cart_checkout_index'] = 0

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(confirm_lbl, callback_data="cart_confirm_all"),
            InlineKeyboardButton(t(lang,'cancel'), callback_data="show_cart_cb")
        ]
    ])
    try:
        await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=kb)
    except BadRequest:
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=kb)
    await update.callback_query.answer()


async def cart_confirm_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء إدخال معرفات كل منتج في السلة."""
    items = context.user_data.get('cart_checkout_items', [])
    idx = context.user_data.get('cart_checkout_index', 0)

    if idx >= len(items):
        lang_done = await get_user_language_db(update.effective_user.id)
        done_msg = "✅ " + ("تم إتمام جميع الطلبات!" if lang_done=='ar' else "All orders placed!" if lang_done=='en' else "هەموو داواکارییەکان تەواوبوون!")
        await update.callback_query.message.reply_text(done_msg, parse_mode=ParseMode.HTML)
        await clear_user_cart_db(update.effective_user.id)
        context.user_data.clear()
        return ConversationHandler.END

    item = items[idx]
    await update.callback_query.edit_message_text(
        f"🎮 أرسل معرف اللاعب للمنتج:\n<b>{escape_html(item['name'])}</b>\n\nلإلغاء: /cancel",
        parse_mode=ParseMode.HTML
    )
    await update.callback_query.answer()
    return CART_CHECKOUT_CONFIRM


async def cart_receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال معرف لعبة لمنتج من السلة."""
    game_id = update.message.text.strip()
    items = context.user_data.get('cart_checkout_items', [])
    idx = context.user_data.get('cart_checkout_index', 0)
    item = items[idx]

    context.user_data['purchase_product_name'] = item['name']
    context.user_data['purchase_price'] = item['price']
    context.user_data['discount'] = 0
    context.user_data['coupon_code'] = None
    context.user_data['flash_offer'] = None

    await complete_purchase(update, context, game_id, is_callback=False)

    context.user_data['cart_checkout_index'] = idx + 1
    next_idx = idx + 1

    if next_idx >= len(items):
        await clear_user_cart_db(update.effective_user.id)
        lang_done2 = await get_user_language_db(update.effective_user.id)
        done_msg2 = "✅ " + ("تم إتمام جميع الطلبات بنجاح!" if lang_done2=='ar' else "All orders completed successfully!" if lang_done2=='en' else "هەموو داواکارییەکان بەسەرکەوتوویی تەواوبوون!")
        await update.message.reply_text(done_msg2, parse_mode=ParseMode.HTML)
        context.user_data.clear()
        return ConversationHandler.END

    next_item = items[next_idx]
    await update.message.reply_text(
        f"🎮 الآن أرسل معرف اللاعب للمنتج التالي:\n<b>{escape_html(next_item['name'])}</b>",
        parse_mode=ParseMode.HTML
    )
    return CART_CHECKOUT_CONFIRM


# ==========================================
# فاتورة PDF
# ==========================================

async def generate_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """توليد فاتورة PDF لطلب."""
    import io
    data = update.callback_query.data.replace("invoice_", "")
    purchase = await get_purchase_by_id_db(data)

    if not purchase:
        await update.callback_query.answer("❌ الطلب غير موجود.", show_alert=True)
        return

    await update.callback_query.answer("⏳ جاري إنشاء الفاتورة...")

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4

        # خلفية
        c.setFillColor(colors.HexColor('#1a1a2e'))
        c.rect(0, 0, w, h, fill=1)

        # شريط علوي
        c.setFillColor(colors.HexColor('#16213e'))
        c.rect(0, h-100, w, 100, fill=1)

        # العنوان
        c.setFillColor(colors.HexColor('#e94560'))
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(w/2, h-65, "INVOICE")

        c.setFillColor(colors.white)
        c.setFont("Helvetica", 12)
        c.drawCentredString(w/2, h-85, "MasterTech Store")

        # خط فاصل
        c.setStrokeColor(colors.HexColor('#e94560'))
        c.setLineWidth(2)
        c.line(50, h-115, w-50, h-115)

        # تفاصيل الفاتورة
        details = [
            ("Invoice #", purchase['purchase_id'][:12].upper()),
            ("Date", str(purchase['timestamp'])[:10]),
            ("Customer", purchase.get('username','N/A')),
            ("Product", purchase['product_name']),
            ("Game ID", purchase['game_id']),
            ("Amount", f"${purchase['price']:.2f}"),
            ("Status", purchase['status'].upper()),
        ]

        y = h - 160
        for label, value in details:
            c.setFillColor(colors.HexColor('#a0a0b0'))
            c.setFont("Helvetica", 11)
            c.drawString(70, y, label + ":")
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(220, y, str(value)[:40])
            y -= 35

        # صندوق المجموع
        c.setFillColor(colors.HexColor('#e94560'))
        c.roundRect(50, 180, w-100, 60, 8, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(w/2, 220, f"TOTAL: ${purchase['price']:.2f}")

        # تذييل
        c.setFillColor(colors.HexColor('#a0a0b0'))
        c.setFont("Helvetica", 10)
        c.drawCentredString(w/2, 80, "Thank you for your purchase!")
        c.drawCentredString(w/2, 60, "t.me/shadowstoresh")

        c.save()
        buf.seek(0)

        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=buf,
            filename=f"invoice_{purchase['purchase_id'][:8]}.pdf",
            caption=f"🧾 فاتورة طلبك #{purchase['purchase_id'][:8]}"
        )
    except ImportError:
        # إذا لم تكن مكتبة reportlab موجودة، أرسل نصاً بديلاً
        txt = (
            f"🧾 فاتورة طلب\n"
            f"{'='*30}\n"
            f"رقم الطلب: {purchase['purchase_id'][:12]}\n"
            f"التاريخ:   {str(purchase['timestamp'])[:10]}\n"
            f"المنتج:    {purchase['product_name']}\n"
            f"المعرف:    {purchase['game_id']}\n"
            f"المبلغ:    ${purchase['price']:.2f}\n"
            f"الحالة:    {purchase['status']}\n"
            f"{'='*30}\n"
            f"شكراً لتسوقك معنا!"
        )
        buf = io.BytesIO(txt.encode('utf-8'))
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=buf,
            filename=f"invoice_{purchase['purchase_id'][:8]}.txt",
            caption=f"🧾 فاتورة طلبك"
        )


# --- دوال القناة ---

async def publish_to_channel(context, message: str, keyboard=None) -> bool:
    """نشر رسالة في قناة التيليغرام."""
    if not CHANNEL_ID:
        return False
    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        return True
    except Exception as e:
        logger.error(f"Failed to publish to channel: {e}")
        return False


async def publish_flash_offer_to_channel(context, name: str, original: float, discounted: float, hours: float, product_id: str):
    """نشر عرض جديد في القناة."""
    discount_pct = int((1 - discounted / original) * 100)
    bot_info = await context.bot.get_me()
    bot_link = f"https://t.me/{bot_info.username}"

    msg = (
        "⚡ <b>عرض محدود الوقت!</b>\n\n"
        f"📦 <b>{escape_html(name)}</b>\n"
        f"💰 <s>${original:.2f}</s> ← <b>${discounted:.2f}</b>\n"
        f"🔥 خصم <b>{discount_pct}%</b>\n"
        f"⏰ ينتهي خلال: <b>{int(hours)} ساعة</b>\n\n"
        "لا تفوّت الفرصة! 👇"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 اشتر الآن", url=bot_link)]
    ])
    await publish_to_channel(context, msg, keyboard)


async def publish_new_product_to_channel(context, name: str, price: float, category: str = ""):
    """نشر منتج جديد في القناة."""
    bot_info = await context.bot.get_me()
    bot_link = f"https://t.me/{bot_info.username}"

    msg = (
        "🆕 <b>منتج جديد!</b>\n\n"
        f"📦 <b>{escape_html(name)}</b>\n"
        + (f"🗂️ الفئة: {escape_html(category)}\n" if category else "")
        + f"💰 السعر: <b>${price:.2f}</b>\n\n"
        "متوفر الآن في متجرنا 👇"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 تسوق الآن", url=bot_link)]
    ])
    await publish_to_channel(context, msg, keyboard)


async def publish_offer_ended_to_channel(context, name: str):
    """نشر انتهاء عرض في القناة."""
    bot_info = await context.bot.get_me()
    bot_link = f"https://t.me/{bot_info.username}"
    msg = (
        f"⌛ انتهى عرض <b>{escape_html(name)}</b>\n\n"
        "تابع قناتنا لتعرف عن العروض القادمة! 🔔"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ تفضل متجرنا", url=bot_link)]
    ])
    await publish_to_channel(context, msg, keyboard)


async def handle_coupon_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة اختيار الكوبون أو التخطي."""
    query = update.callback_query
    await query.answer()

    if query.data == "skip_coupon":
        context.user_data['discount'] = 0
        context.user_data['coupon_code'] = None
        product_name = context.user_data.get('purchase_product_name', '')
        price = context.user_data.get('purchase_price', 0)
        await query.message.reply_text(
            f"🎮 يرجى إرسال معرف اللاعب (ID) الخاص بك:\n\n"
            f"المنتج: <b>{escape_html(product_name)}</b>\n"
            f"السعر: <b>${price:.2f}</b>\n\n"
            f"لإلغاء العملية، أرسل /cancel",
            parse_mode=ParseMode.HTML
        )
        return ASK_GAME_ID

    elif query.data == "apply_coupon":
        await query.message.reply_text(
            "🎟️ أرسل كود الكوبون:\n\n"
            "لإلغاء العملية، أرسل /cancel"
        )
        return ASK_COUPON + 1  # ENTER_COUPON_CODE = 31


async def receive_coupon_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال كود الكوبون والتحقق منه."""
    code = update.message.text.strip().upper()
    coupon = await get_coupon_db(code)

    price = context.user_data.get('purchase_price', 0)
    product_name = context.user_data.get('purchase_product_name', '')

    if not coupon:
        await update.message.reply_text(
            "❌ الكوبون غير صحيح أو منتهي الصلاحية.\n\n"
            "يمكنك المتابعة بالسعر الأصلي أو إرسال كود آخر:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏩ متابعة بدون كوبون", callback_data="skip_coupon")]
            ])
        )
        return ASK_COUPON + 1

    # حساب الخصم
    if coupon['discount_type'] == 'percent':
        discount = price * (coupon['discount_value'] / 100)
        discount_text = f"{coupon['discount_value']}%"
    else:
        discount = min(coupon['discount_value'], price)
        discount_text = f"${coupon['discount_value']:.2f}"

    final_price = max(0, price - discount)
    context.user_data['discount'] = discount
    context.user_data['coupon_code'] = code
    context.user_data['purchase_price'] = final_price

    await update.message.reply_text(
        f"✅ تم تطبيق الكوبون <b>{escape_html(code)}</b>!\n\n"
        f"💰 السعر الأصلي: <s>${price:.2f}</s>\n"
        f"🎟️ الخصم: {discount_text}\n"
        f"✨ السعر النهائي: <b>${final_price:.2f}</b>\n\n"
        f"🎮 الآن أرسل معرف اللاعب (ID):\n\n"
        f"المنتج: <b>{escape_html(product_name)}</b>\n\n"
        f"لإلغاء العملية، أرسل /cancel",
        parse_mode=ParseMode.HTML
    )
    return ASK_GAME_ID


# --- إدارة الكوبونات للأدمن ---

async def admin_coupons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """لوحة إدارة الكوبونات."""
    from admin_handlers import is_admin
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    coupons = await get_all_coupons_db()
    msg = "🎟️ <b>إدارة الكوبونات</b>\n\n"
    if coupons:
        for c in coupons:
            status = "✅" if c['is_active'] else "❌"
            dtype = f"{c['discount_value']}%" if c['discount_type'] == 'percent' else f"${c['discount_value']:.2f}"
            msg += f"{status} <code>{c['code']}</code> — خصم {dtype} | الاستخدام: {c['used_count']}/{c['max_uses']}\n"
    else:
        msg += "لا توجد كوبونات حالياً.\n"

    keyboard = [
        [InlineKeyboardButton("➕ إضافة كوبون", callback_data="admin_add_coupon")],
        [InlineKeyboardButton("🗑️ حذف كوبون", callback_data="admin_del_coupon")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")],
    ]
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest:
            await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)


async def admin_add_coupon_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء إضافة كوبون."""
    await update.callback_query.edit_message_text(
        "➕ <b>إضافة كوبون جديد</b>\n\nأرسل كود الكوبون (مثال: SUMMER20):",
        parse_mode=ParseMode.HTML
    )
    await update.callback_query.answer()
    return ADD_COUPON_CODE


async def admin_add_coupon_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_coupon_code'] = update.message.text.strip().upper()
    keyboard = [
        [InlineKeyboardButton("💯 نسبة مئوية (%)", callback_data="coupon_type_percent")],
        [InlineKeyboardButton("💵 مبلغ ثابت ($)", callback_data="coupon_type_fixed")],
    ]
    await update.message.reply_text("اختر نوع الخصم:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_COUPON_TYPE


async def admin_add_coupon_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dtype = "percent" if update.callback_query.data == "coupon_type_percent" else "fixed"
    context.user_data['new_coupon_type'] = dtype
    label = "النسبة المئوية (مثال: 20 لخصم 20%)" if dtype == "percent" else "المبلغ بالدولار (مثال: 2.5)"
    await update.callback_query.edit_message_text(f"أرسل قيمة الخصم — {label}:")
    await update.callback_query.answer()
    return ADD_COUPON_VALUE


async def admin_add_coupon_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = float(update.message.text.strip())
        if val <= 0:
            raise ValueError
        context.user_data['new_coupon_value'] = val
    except ValueError:
        await update.message.reply_text("❌ أدخل رقماً صحيحاً أكبر من الصفر.")
        return ADD_COUPON_VALUE
    await update.message.reply_text("كم مرة يمكن استخدام هذا الكوبون؟ (أرسل رقماً، مثال: 1 أو 100)")
    return ADD_COUPON_USES


async def admin_add_coupon_uses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        uses = int(update.message.text.strip())
        if uses <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ أدخل عدداً صحيحاً أكبر من الصفر.")
        return ADD_COUPON_USES

    code = context.user_data['new_coupon_code']
    dtype = context.user_data['new_coupon_type']
    value = context.user_data['new_coupon_value']

    success = await add_coupon_db(code, dtype, value, uses)
    if success:
        dtype_label = f"{value}%" if dtype == "percent" else f"${value:.2f}"
        await update.message.reply_text(
            f"✅ تم إضافة الكوبون بنجاح!\n\n"
            f"🎟️ الكود: <code>{code}</code>\n"
            f"💰 الخصم: {dtype_label}\n"
            f"🔢 الاستخدامات: {uses}",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text("❌ الكوبون موجود مسبقاً. جرب كوداً آخر.")
    context.user_data.clear()
    return ConversationHandler.END


async def admin_del_coupon_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """حذف كوبون."""
    from admin_handlers import is_admin
    if not is_admin(update.effective_user.id):
        return
    coupons = await get_all_coupons_db()
    if not coupons:
        await update.callback_query.answer("لا توجد كوبونات.", show_alert=True)
        return
    keyboard = [[InlineKeyboardButton(f"🗑️ {c['code']}", callback_data=f"del_coupon_{c['code']}")] for c in coupons]
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_coupons")])
    await update.callback_query.edit_message_text("اختر الكوبون للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
    await update.callback_query.answer()


async def admin_del_coupon_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    code = update.callback_query.data.replace("del_coupon_", "")
    await delete_coupon_db(code)
    await update.callback_query.answer(f"✅ تم حذف {code}", show_alert=True)
    await admin_coupons(update, context)


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
    elif data == "support_menu":
        await support_menu(update, context)
    elif data == "support_new":
        await support_new_start(update, context)
    elif data == "support_my_tickets":
        await support_my_tickets(update, context)
    elif data.startswith("support_view_"):
        await support_view_ticket(update, context)
    elif data == "admin_support":
        await admin_support_panel(update, context)
    elif data.startswith("admin_ticket_"):
        await admin_view_ticket(update, context)
    elif data.startswith("admin_reply_"):
        await admin_reply_start(update, context)
    elif data.startswith("admin_close_"):
        await admin_close_ticket(update, context)
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
    elif data == "admin_stats":
        await stats(update, context)
    elif data == "admin_pending_orders":
        await admin_pending_orders(update, context)
    elif data == "admin_pending_deposits":
        await admin_pending_deposits(update, context)
    elif data == "admin_search_user":
        await admin_search_user_start(update, context)
    elif data == "admin_set_balance":
        await admin_set_balance_start(update, context)
    elif data.startswith("confirm_ship_"):
        await admin_confirm_ship_btn(update, context)
    elif data.startswith("confirm_dep_"):
        await admin_confirm_dep_btn(update, context)
    elif data == "admin_coupons":
        await admin_coupons(update, context)
    elif data == "admin_add_coupon":
        await admin_add_coupon_start(update, context)
    elif data == "admin_del_coupon":
        await admin_del_coupon_start(update, context)
    elif data.startswith("del_coupon_"):
        await admin_del_coupon_confirm(update, context)
    elif data in ["apply_coupon", "skip_coupon"]:
        await handle_coupon_choice(update, context)
    elif data.startswith("set_currency_"):
        await handle_set_currency(update, context)
    elif data == "show_language":
        await show_language_settings(update, context)
    elif data.startswith("set_lang_"):
        await handle_set_language(update, context)
    elif data == "toggle_2fa":
        await toggle_2fa(update, context)
    elif data == "confirm_2fa_purchase":
        game_id = context.user_data.get('pending_game_id_2fa','')
        if game_id: await complete_purchase(update, context, game_id, is_callback=True)
    elif data.startswith("reorder_"):
        await reorder(update, context)
    elif data.startswith("invoice_"):
        await generate_invoice(update, context)
    elif data.startswith("refund_select_"):
        context.user_data['refund_purchase_id'] = data.replace('refund_select_','')
        await update.callback_query.edit_message_text(
            '💸 <b>طلب استرداد</b>\n\nأرسل <b>سبب</b> طلب الاسترداد:\n\nلإلغاء: /cancel',
            parse_mode=ParseMode.HTML)
        await update.callback_query.answer()
        context.user_data['awaiting_refund_reason'] = True
    elif data.startswith("refund_approve_") or data.startswith("refund_reject_"):
        await admin_process_refund(update, context)
    elif data == "cart_confirm_all":
        await cart_confirm_all(update, context)
    elif data == "show_refund":
        await show_refund_options(update, context)
    elif data == "cart_checkout":
        await cart_checkout(update, context)
    elif data == "user_settings":
        await show_settings(update, context)
    elif data == "admin_set_rate":
        await admin_set_rate_start(update, context)
    elif data == "show_referral":
        await show_referral(update, context)
    elif data == "show_flash_offers":
        await show_flash_offers(update, context)
    elif data == "admin_flash_offers":
        await admin_flash_offers(update, context)
    elif data == "admin_add_offer":
        await admin_add_offer_start(update, context)
    elif data == "admin_cancel_offer":
        await admin_cancel_offer(update, context)
    elif data.startswith("del_offer_"):
        await admin_del_offer_confirm(update, context)
    elif data == "admin_ref_reward":
        await admin_set_ref_reward_start(update, context)
    else:
        await query.answer("❌ أمر غير معروف.")


async def admin_announce(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نشر إعلان يدوي في القناة — /announce النص"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return
    if not context.args:
        await update.message.reply_text(
            "📢 الاستخدام:\n<code>/announce نص الإعلان هنا</code>",
            parse_mode=ParseMode.HTML
        )
        return
    text = " ".join(context.args)
    bot_info = await context.bot.get_me()
    bot_link = f"https://t.me/{bot_info.username}"
    msg = f"📢 <b>إعلان</b>\n\n{escape_html(text)}"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ المتجر", url=bot_link)]])
    success = await publish_to_channel(context, msg, keyboard)
    if success:
        await update.message.reply_text("✅ تم نشر الإعلان في القناة!")
    else:
        await update.message.reply_text("❌ فشل النشر، تأكد أن البوت أدمن في القناة.")


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

    # محادثات الشراء (مع الكوبونات)
    purchase_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(request_game_id, pattern='^buy_')
        ],
        states={
            ASK_COUPON: [CallbackQueryHandler(handle_coupon_choice, pattern='^(apply_coupon|skip_coupon)$')],
            ASK_COUPON + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_coupon_code)],
            CHOOSE_SAVED_GAME_ID: [CallbackQueryHandler(handle_saved_game_id_choice)],
            ASK_GAME_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_game_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(purchase_handler)

    # محادثات إضافة كوبون
    coupon_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_coupon_start, pattern='^admin_add_coupon$')],
        states={
            ADD_COUPON_CODE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_coupon_code)],
            ADD_COUPON_TYPE:  [CallbackQueryHandler(admin_add_coupon_type, pattern='^coupon_type_')],
            ADD_COUPON_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_coupon_value)],
            ADD_COUPON_USES:  [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_coupon_uses)],
        },
        fallbacks=[CommandHandler("cancel", cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(coupon_handler)

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
    application.add_handler(CommandHandler("announce", admin_announce))
    application.add_handler(CommandHandler("setrate", admin_set_rate_start))

    # محادثة تحديث سعر الصرف
    set_rate_handler = ConversationHandler(
        entry_points=[
            CommandHandler("setrate", admin_set_rate_start),
            CallbackQueryHandler(admin_set_rate_start, pattern='^admin_set_rate$'),
        ],
        states={
            ADMIN_SET_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_rate_receive)],
        },
        fallbacks=[CommandHandler("cancel", cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(set_rate_handler)

    # محادثة تعديل رصيد مستخدم
    set_balance_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_set_balance_start, pattern='^admin_set_balance$')],
        states={
            ADMIN_SET_BALANCE_USER:   [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_balance_user)],
            ADMIN_SET_BALANCE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_balance_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(set_balance_handler)

    # محادثة إضافة عرض
    flash_offer_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_offer_start, pattern='^admin_add_offer$')],
        states={
            ADD_OFFER_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_offer_product)],
            ADD_OFFER_PRICE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_offer_price)],
            ADD_OFFER_HOURS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_offer_hours)],
        },
        fallbacks=[CommandHandler('cancel', cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(flash_offer_handler)

    # محادثة تعديل مكافأة الإحالة
    ref_reward_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_set_ref_reward_start, pattern='^admin_ref_reward$')],
        states={
            ADMIN_SET_REF_REWARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_ref_reward_receive)],
        },
        fallbacks=[CommandHandler('cancel', cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(ref_reward_handler)

    # محادثات دعم العملاء
    support_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(support_new_start, pattern='^support_new$')],
        states={
            SUPPORT_SUBJECT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, support_receive_subject)],
            SUPPORT_MESSAGE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, support_receive_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(support_handler)

    # محادثة رد الأدمن
    admin_reply_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_reply_start, pattern='^admin_reply_')],
        states={
            SUPPORT_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply_send)],
        },
        fallbacks=[CommandHandler('cancel', cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(admin_reply_handler)

    # محادثة الاسترداد
    refund_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(refund_select, pattern='^refund_select_')],
        states={
            REFUND_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, refund_receive_reason)],
        },
        fallbacks=[CommandHandler('cancel', cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(refund_handler)

    # محادثة checkout السلة
    cart_checkout_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(cart_confirm_all, pattern='^cart_confirm_all$')],
        states={
            CART_CHECKOUT_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, cart_receive_game_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel_deposit)],
        allow_reentry=True
    )
    application.add_handler(cart_checkout_handler)
    application.add_handler(CommandHandler("admin_confirm_deposit", admin_confirm_deposit))
    application.add_handler(CommandHandler("admin_confirm_shipped", admin_confirm_shipped))
    application.add_handler(CommandHandler("delete_product", admin_delete_product))

    # معالجة ضغطات الأزرار
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # معالجة الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"🤖 تم تشغيل بوت {WEBSITE_NAME} بنجاح! (النسخة المحسنة)")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def _init():
    init_db()
    await init_referral_tables()
    await init_support_table()
    # إنشاء جدول الاسترداد
    import sqlite3 as _sq
    from config import DATABASE_NAME as _DB
    conn = _sq.connect(_DB)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS refund_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    import asyncio
    asyncio.get_event_loop().run_until_complete(_init())
    main()
