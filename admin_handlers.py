# admin_handlers.py
"""
معالجات خاصة بالمسؤول لإدارة المنتجات والفئات
"""

import logging
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

from config import ADMIN_USER_ID
from database import (
    add_category_db, get_all_categories_db, update_category_db, delete_category_db,
    add_subcategory_db, get_subcategories_by_category_db,
    add_server_db, get_servers_by_subcategory_db,
    add_product_db, get_products_by_parent_db, update_product_db, delete_product_db,
    get_product_by_id_db
)

logger = logging.getLogger(__name__)

# حالات المحادثة لإضافة منتج
ADD_PRODUCT_NAME, ADD_PRODUCT_PRICE, ADD_PRODUCT_DESC, ADD_PRODUCT_CATEGORY, ADD_PRODUCT_SUBCATEGORY, ADD_PRODUCT_SERVER = range(6, 12)

# حالات المحادثة لإضافة فئة
ADD_CATEGORY_NAME, ADD_CATEGORY_DESC = range(12, 14)

# حالات المحادثة لتعديل السعر
EDIT_PRODUCT_PRICE = 14

def is_admin(user_id: int) -> bool:
    """التحقق من صلاحيات المسؤول."""
    return user_id == ADMIN_USER_ID

def escape_html(text: str | None) -> str:
    """Helper function to escape HTML characters."""
    if text is None:
        return ""
    return html.escape(str(text))


# --- لوحة التحكم الرئيسية ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض لوحة تحكم المسؤول."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ هذا الأمر مخصص للمسؤول فقط.")
        return

    keyboard = [
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("⏳ الطلبات المعلقة", callback_data="admin_pending_orders"),
         InlineKeyboardButton("💳 الإيداعات", callback_data="admin_pending_deposits")],
        [InlineKeyboardButton("➕ إضافة فئة", callback_data="admin_add_category"),
         InlineKeyboardButton("📋 الفئات", callback_data="admin_list_categories")],
        [InlineKeyboardButton("➕ إضافة منتج", callback_data="admin_add_product_start"),
         InlineKeyboardButton("📦 المنتجات", callback_data="admin_list_products")],
        [InlineKeyboardButton("✏️ تعديل منتج", callback_data="admin_edit_product_start"),
         InlineKeyboardButton("🗑️ حذف منتج", callback_data="admin_delete_product_start")],
        [InlineKeyboardButton("🎟️ الكوبونات", callback_data="admin_coupons"),
         InlineKeyboardButton("💰 تعديل رصيد", callback_data="admin_set_balance")],
        [InlineKeyboardButton("👤 بحث مستخدم", callback_data="admin_search_user")],
        [InlineKeyboardButton("💱 سعر الصرف", callback_data="admin_set_rate"),
         InlineKeyboardButton("⚡ العروض", callback_data="admin_flash_offers")],
        [InlineKeyboardButton("🎁 مكافأة الإحالة", callback_data="admin_ref_reward")],
        [InlineKeyboardButton("📢 نشر إعلان", callback_data="admin_announce_prompt")],
        [InlineKeyboardButton("🎫 تذاكر الدعم", callback_data="admin_support")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ]

    message = "🎛️ لوحة تحكم المسؤول\n\nاختر العملية التي تريد القيام بها:"

    if update.message:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            
        )
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                
            )
        except BadRequest:
            await update.callback_query.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                
            )

# --- إدارة الفئات ---

async def admin_add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية إضافة فئة."""
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    await update.callback_query.message.reply_text(
        "➕ إضافة فئة جديدة\n\nيرجى إرسال اسم الفئة:\n\nلإلغاء العملية، أرسل /cancel",
        
    )
    await update.callback_query.answer()
    return ADD_CATEGORY_NAME

async def admin_add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال اسم الفئة."""
    category_name = update.message.text
    context.user_data['new_category_name'] = category_name

    await update.message.reply_text(
        f"اسم الفئة: {escape_html(category_name)}\n\nيرجى إرسال وصف الفئة (اختياري):\n\nلتخطي الوصف، أرسل: skip\nلإلغاء العملية، أرسل: /cancel",
        
    )
    return ADD_CATEGORY_DESC

async def admin_add_category_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال وصف الفئة وإتمام الإضافة."""
    category_desc = update.message.text if update.message.text.lower() != "skip" else None
    category_name = context.user_data.get('new_category_name')

    # توليد معرف تلقائي
    import uuid
    category_id = f"cat_{uuid.uuid4().hex[:8]}"

    # إضافة الفئة إلى قاعدة البيانات
    success = await add_category_db(category_id, category_name, category_desc)

    if success:
        await update.message.reply_text(
            f"✅ تم إضافة الفئة بنجاح!\n\nالاسم: {escape_html(category_name)}\nالمعرف: {escape_html(category_id)}",
            
        )
    else:
        await update.message.reply_text("❌ حدث خطأ أثناء إضافة الفئة. ربما المعرف مكرر.")

    context.user_data.clear()
    return ConversationHandler.END

async def admin_list_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض جميع الفئات."""
    if not is_admin(update.effective_user.id):
        return

    categories = await get_all_categories_db(active_only=False)

    if not categories:
        message = "لا توجد فئات حالياً."
    else:
        message = "📋 قائمة الفئات:\n\n"
        for cat in categories:
            status = "✅" if cat['is_active'] else "❌"
            message += f"{status} {escape_html(cat['name'])}\n"
            message += f"   المعرف: {escape_html(cat['category_id'])}\n"
            if cat['description']:
                message += f"   الوصف: {escape_html(cat['description'])}\n"
            message += "\n"

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                
            )
        except BadRequest:
            await update.callback_query.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                
            )

# --- إدارة المنتجات ---

async def admin_add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية إضافة منتج."""
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    await update.callback_query.message.reply_text(
        "➕ إضافة منتج جديد\n\nيرجى إرسال اسم المنتج:\n\nلإلغاء العملية، أرسل /cancel",
        
    )
    await update.callback_query.answer()
    return ADD_PRODUCT_NAME

async def admin_add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال اسم المنتج."""
    product_name = update.message.text
    context.user_data['new_product_name'] = product_name

    await update.message.reply_text(
        f"اسم المنتج: {escape_html(product_name)}\n\nيرجى إرسال سعر المنتج (بالدولار):",
        
    )
    return ADD_PRODUCT_PRICE

async def admin_add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال سعر المنتج."""
    try:
        price = float(update.message.text)
        if price <= 0:
            await update.message.reply_text("❌ يرجى إدخال سعر صحيح أكبر من الصفر.")
            return ADD_PRODUCT_PRICE
        context.user_data['new_product_price'] = price
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال السعر كأرقام فقط.")
        return ADD_PRODUCT_PRICE

    await update.message.reply_text(
        f"السعر: ${price:.2f}\n\nيرجى إرسال وصف المنتج (اختياري):\n\nلتخطي الوصف، أرسل: skip",
        
    )
    return ADD_PRODUCT_DESC

async def admin_add_product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال وصف المنتج واختيار الفئة."""
    product_desc = update.message.text if update.message.text.lower() != "skip" else None
    context.user_data['new_product_desc'] = product_desc

    # عرض الفئات المتاحة
    categories = await get_all_categories_db(active_only=True)

    if not categories:
        await update.message.reply_text("❌ لا توجد فئات متاحة. يرجى إضافة فئة أولاً.")
        context.user_data.clear()
        return ConversationHandler.END

    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(cat['name'], callback_data=f"addprod_cat_{cat['category_id']}")])

    await update.message.reply_text(
        "يرجى اختيار الفئة التي ينتمي إليها المنتج:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADD_PRODUCT_CATEGORY

async def admin_add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال اختيار الفئة."""
    query = update.callback_query
    category_id = query.data.replace("addprod_cat_", "")
    context.user_data['new_product_category_id'] = category_id

    # التحقق من وجود فئات فرعية
    subcategories = await get_subcategories_by_category_db(category_id, active_only=True)

    if subcategories:
        keyboard = []
        for subcat in subcategories:
            keyboard.append([InlineKeyboardButton(subcat['name'], callback_data=f"addprod_subcat_{subcat['subcategory_id']}")])
        keyboard.append([InlineKeyboardButton("⏭️ تخطي (بدون فئة فرعية)", callback_data="addprod_subcat_skip")])

        await query.message.reply_text(
            "يرجى اختيار الفئة الفرعية:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADD_PRODUCT_SUBCATEGORY
    else:
        # لا توجد فئات فرعية، إتمام الإضافة
        await finalize_add_product(update, context)
        return ConversationHandler.END

async def admin_add_product_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال اختيار الفئة الفرعية."""
    query = update.callback_query
    
    if query.data == "addprod_subcat_skip":
        context.user_data['new_product_subcategory_id'] = None
        await finalize_add_product(update, context)
        return ConversationHandler.END
    
    subcategory_id = query.data.replace("addprod_subcat_", "")
    context.user_data['new_product_subcategory_id'] = subcategory_id

    # التحقق من وجود سيرفرات
    servers = await get_servers_by_subcategory_db(subcategory_id, active_only=True)

    if servers:
        keyboard = []
        for server in servers:
            keyboard.append([InlineKeyboardButton(server['name'], callback_data=f"addprod_server_{server['server_id']}")])
        keyboard.append([InlineKeyboardButton("⏭️ تخطي (بدون سيرفر)", callback_data="addprod_server_skip")])

        await query.message.reply_text(
            "يرجى اختيار السيرفر:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADD_PRODUCT_SERVER
    else:
        await finalize_add_product(update, context)
        return ConversationHandler.END

async def admin_add_product_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال اختيار السيرفر."""
    query = update.callback_query
    
    if query.data == "addprod_server_skip":
        context.user_data['new_product_server_id'] = None
    else:
        server_id = query.data.replace("addprod_server_", "")
        context.user_data['new_product_server_id'] = server_id

    await finalize_add_product(update, context)
    return ConversationHandler.END

async def finalize_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إتمام عملية إضافة المنتج."""
    import uuid
    product_id = f"prod_{uuid.uuid4().hex[:8]}"
    
    product_name = context.user_data.get('new_product_name')
    product_price = context.user_data.get('new_product_price')
    product_desc = context.user_data.get('new_product_desc')
    category_id = context.user_data.get('new_product_category_id')
    subcategory_id = context.user_data.get('new_product_subcategory_id')
    server_id = context.user_data.get('new_product_server_id')

    success = await add_product_db(
        product_id=product_id,
        name=product_name,
        price=product_price,
        description=product_desc,
        category_id=category_id,
        subcategory_id=subcategory_id,
        server_id=server_id,
        requires_game_id=1  # افتراضياً يتطلب معرف لعبة
    )

    if success:
        message = f"✅ تم إضافة المنتج بنجاح!\n\n"
        message += f"الاسم: {escape_html(product_name)}\n"
        message += f"السعر: ${product_price:.2f}\n"
        message += f"المعرف: {escape_html(product_id)}"
        
        if update.callback_query:
            await update.callback_query.message.reply_text(message, )
        else:
            await update.message.reply_text(message, )
    else:
        error_msg = "❌ حدث خطأ أثناء إضافة المنتج."
        if update.callback_query:
            await update.callback_query.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)

    context.user_data.clear()

async def admin_list_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض جميع المنتجات."""
    if not is_admin(update.effective_user.id):
        return

    categories = await get_all_categories_db(active_only=False)
    
    message = "📦 قائمة المنتجات:\n\n"
    
    for cat in categories:
        products = await get_products_by_parent_db(cat['category_id'], "category", active_only=False)
        if products:
            message += f"{escape_html(cat['name'])}:\n"
            for prod in products:
                status = "✅" if prod['is_active'] else "❌"
                message += f"  {status} {escape_html(prod['name'])} - ${prod['price']:.2f}\n"
                message += f"     ID: {escape_html(prod['product_id'])}\n"
            message += "\n"

    if message == "📦 قائمة المنتجات:\n\n":
        message = "لا توجد منتجات حالياً."

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                
            )
        except BadRequest:
            await update.callback_query.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                
            )

async def admin_edit_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء عملية تعديل منتج."""
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    await update.callback_query.message.reply_text(
        "✏️ تعديل منتج\n\nيرجى إرسال معرف المنتج (Product ID) الذي تريد تعديله:\n\nلإلغاء العملية، أرسل /cancel",
        
    )
    await update.callback_query.answer()
    return EDIT_PRODUCT_PRICE

async def admin_edit_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استقبال معرف المنتج والسعر الجديد."""
    parts = update.message.text.split()
    
    if len(parts) != 2:
        await update.message.reply_text(
            "❌ صيغة غير صحيحة. يرجى إرسال: product_id new_price\n\nمثال: prod_abc123 9.99",
            
        )
        return EDIT_PRODUCT_PRICE
    
    product_id = parts[0]
    try:
        new_price = float(parts[1])
        if new_price <= 0:
            await update.message.reply_text("❌ يرجى إدخال سعر صحيح أكبر من الصفر.")
            return EDIT_PRODUCT_PRICE
    except ValueError:
        await update.message.reply_text("❌ السعر يجب أن يكون رقماً.")
        return EDIT_PRODUCT_PRICE

    # التحقق من وجود المنتج
    product = await get_product_by_id_db(product_id)
    if not product:
        await update.message.reply_text(f"❌ المنتج بالمعرف {escape_html(product_id)} غير موجود.", )
        return ConversationHandler.END

    # تحديث السعر
    success = await update_product_db(product_id, price=new_price)
    
    if success:
        await update.message.reply_text(
            f"✅ تم تحديث سعر المنتج بنجاح!\n\n"
            f"المنتج: {escape_html(product['name'])}\n"
            f"السعر القديم: ${product['price']:.2f}\n"
            f"السعر الجديد: ${new_price:.2f}",
            
        )
    else:
        await update.message.reply_text("❌ حدث خطأ أثناء تحديث السعر.")

    return ConversationHandler.END

async def admin_delete_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """حذف منتج (soft delete)."""
    if not is_admin(update.effective_user.id):
        return

    await update.callback_query.message.reply_text(
        "🗑️ حذف منتج\n\nلحذف منتج، استخدم الأمر:\n/delete_product product_id\n\nمثال: /delete_product prod_abc123",
        
    )
    await update.callback_query.answer()

async def admin_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تنفيذ حذف المنتج."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ هذا الأمر مخصص للمسؤول فقط.")
        return

    try:
        product_id = update.message.text.split()[1]
    except IndexError:
        await update.message.reply_text("❌ صيغة غير صحيحة. الاستخدام: /delete_product product_id", )
        return

    product = await get_product_by_id_db(product_id)
    if not product:
        await update.message.reply_text(f"❌ المنتج بالمعرف {escape_html(product_id)} غير موجود.", )
        return

    success = await delete_product_db(product_id)
    
    if success:
        await update.message.reply_text(
            f"✅ تم حذف المنتج بنجاح!\n\nالمنتج: {escape_html(product['name'])}",
            
        )
    else:
        await update.message.reply_text("❌ حدث خطأ أثناء حذف المنتج.")

async def cancel_admin_operation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء العملية الإدارية."""
    await update.message.reply_text("❌ تم إلغاء العملية.")
    context.user_data.clear()
    return ConversationHandler.END
