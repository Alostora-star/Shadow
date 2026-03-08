# translations.py — ترجمة كاملة للبوت

TRANSLATIONS = {
    'ar': {
        # عام
        'welcome': 'مرحباً بك في <b>{name}</b>!\n\n{slogan}',
        'unknown_cmd': 'عذراً، لم أفهم طلبك. يرجى استخدام الأزرار في القائمة الرئيسية.',
        'back': '⬅️ رجوع',
        'cancel': '❌ إلغاء',
        'confirm': '✅ تأكيد',
        'main_menu_btn': '🏠 القائمة الرئيسية',
        'admin_only': '❌ هذا الأمر مخصص للمسؤول فقط.',
        'error_generic': '❌ حدث خطأ. حاول مجدداً.',

        # المحفظة
        'wallet_title': '💰 محفظتك',
        'wallet_balance': 'رصيدك الحالي: <b>{balance}</b>',
        'wallet_choose_method': 'اختر طريقة الإيداع:',
        'wallet_insufficient': '❌ رصيدك غير كافٍ. السعر: {price}، رصيدك: {balance}',
        'deposit_confirmed': '✅ تم تأكيد إيداعك!\n\nتم إضافة <b>{amount}</b> إلى محفظتك.\nرصيدك الحالي: <b>{balance}</b>',

        # الشراء
        'buy_now': '🛒 شراء الآن',
        'add_to_cart': '🛒 أضف للسلة',
        'coupon_ask': 'هل لديك كوبون خصم؟',
        'coupon_have': '🎟️ لدي كوبون خصم',
        'coupon_skip': '⏩ تخطي',
        'enter_game_id': '🎮 يرجى إرسال معرف اللاعب (ID) الخاص بك:\n\n<b>المنتج:</b> {product}\n<b>السعر:</b> {price}',
        'purchase_success': '✅ <b>تم الشراء بنجاح!</b>\n\n📦 المنتج: {product}\n🎮 المعرف: <code>{game_id}</code>\n💰 المبلغ: {price}\n👛 رصيدك المتبقي: {balance}',
        'purchase_cancelled': '❌ تم إلغاء عملية الشراء.',
        'save_game_id': '💾 هل تريد حفظ هذا المعرف للمرة القادمة؟',
        'save_yes': '✅ نعم',
        'save_no': '❌ لا',
        'game_id_saved': '✅ تم حفظ المعرف!',
        'confirm_purchase_title': '⚠️ تأكيد الشراء',
        'confirm_purchase_msg': 'هل تريد تأكيد شراء:\n\n📦 {product}\n💰 {price}\n🎮 المعرف: <code>{game_id}</code>',

        # الطلبات
        'orders_title': '📋 <b>طلباتي</b> ({count} طلب)',
        'orders_empty': '📋 <b>طلباتي</b>\n\nلا توجد طلبات سابقة حتى الآن.',
        'order_shipped': '✅ <b>تمت عملية الشحن!</b>\n\n📦 المنتج: {product}\n🎮 المعرف: <code>{game_id}</code>\n\nشكراً لتسوقك معنا! 🙏',
        'status_pending': '⏳ قيد التنفيذ',
        'status_shipped': '✅ تم الشحن',
        'status_completed': '✅ مكتمل',
        'status_cancelled': '❌ ملغي',
        'status_refunded': '💸 مسترد',
        'status_refund_req': '🔄 طلب استرداد',

        # الكوبون
        'coupon_enter': '🎟️ أرسل رمز الكوبون:',
        'coupon_invalid': '❌ الكوبون غير صحيح أو منتهي الصلاحية.',
        'coupon_applied': '✅ تم تطبيق الكوبون!\n\n💰 الخصم: {discount}\n💵 السعر بعد الخصم: {price}',

        # الإعدادات
        'settings_title': '⚙️ <b>إعداداتي</b>',
        'settings_name': '👤 الاسم: <b>{name}</b>',
        'settings_balance': '💰 الرصيد: <b>{balance}</b>',
        'settings_currency': '💱 العملة: <b>{currency}</b>',
        'settings_rate': '📈 سعر الصرف: <b>1$ = {rate} ل.س</b>',
        'settings_lang': '🌍 اللغة: <b>{lang}</b>',
        'settings_2fa': '🔐 التحقق بخطوتين: <b>{status}</b>',
        '2fa_on': 'مفعّل ✅',
        '2fa_off': 'معطّل ❌',
        'change_language': '🌍 تغيير اللغة',
        'enable_2fa': '🔓 تفعيل التحقق بخطوتين',
        'disable_2fa': '🔒 إيقاف التحقق بخطوتين',
        'language_changed': '✅ تم تغيير اللغة إلى العربية',
        'two_fa_enabled': '✅ تم تفعيل التحقق بخطوتين\n\nسيُطلب تأكيدك قبل كل عملية شراء فوق $2.',
        'two_fa_disabled': '✅ تم إيقاف التحقق بخطوتين',
        'currency_usd': '🇺🇸 دولار USD',
        'currency_syp': '🇸🇾 ليرة SYP',

        # الإحالة
        'referral_title': '🔗 <b>نظام الإحالة</b>',
        'referral_desc': 'شارك رابطك الخاص مع أصدقائك.\nعند أول شراء لكل صديق تحصل على <b>{reward}</b>!',
        'referral_link': '🔗 رابطك الخاص:',
        'referral_stats': '📊 <b>إحصائياتك:</b>\n👥 الأصدقاء المدعوين: <b>{total}</b>\n💰 مكافآت محصّلة: <b>{paid}</b> ({amount})',
        'referral_reward_msg': '🎉 <b>مكافأة إحالة!</b>\n\nقام صديقك بأول عملية شراء!\n💰 تم إضافة <b>{reward}</b> إلى محفظتك!',

        # العروض
        'offers_title': '⚡ <b>العروض المحدودة</b>',
        'offers_empty': '⚡ <b>العروض المحدودة</b>\n\nلا توجد عروض نشطة حالياً.\nتابع البوت لتعرف عن العروض القادمة!',
        'offer_expires': '⏰ ينتهي خلال: <b>{hours}س {mins}د</b>',
        'flash_label': '🔥 <b>عرض محدود!</b> ينتهي خلال {hours}س {mins}د',
        'shop_now': '🛒 تسوق الآن',

        # الدعم
        'support_title': '💬 <b>دعم العملاء</b>',
        'support_desc': 'هل لديك مشكلة أو استفسار؟ افتح تذكرة وسيرد عليك فريق الدعم.',
        'support_stats': '📋 تذاكرك: <b>{total}</b> | مفتوحة: <b>{open}</b>',
        'new_ticket': '➕ تذكرة جديدة',
        'my_tickets': '📋 تذاكري',
        'ticket_subject_ask': '➕ <b>تذكرة جديدة</b>\n\nأرسل <b>موضوع</b> مشكلتك باختصار:\n\nللإلغاء: /cancel',
        'ticket_subject_short': '❌ الموضوع قصير جداً. أرسل وصفاً أوضح:',
        'ticket_msg_ask': '📝 الموضوع: <b>{subject}</b>\n\nالآن أرسل <b>تفاصيل</b> مشكلتك:',
        'ticket_created': '✅ <b>تم إرسال تذكرتك!</b>\n\nرقم التذكرة: <b>#{id}</b>\nسيرد عليك فريق الدعم قريباً. 🙏',
        'ticket_reply': '💬 <b>رد جديد على تذكرتك #{id}</b>\n\n📌 {subject}\n\n🛡️ <b>الدعم:</b>\n{reply}',
        'ticket_closed_msg': '✅ <b>تم إغلاق تذكرتك #{id}</b>\n\nنأمل أننا تمكنا من مساعدتك! 🙏',

        # الاسترداد
        'refund_title': '💸 <b>طلب استرداد</b>',
        'refund_no_orders': '❌ لا توجد طلبات مؤهلة للاسترداد.',
        'refund_select': 'اختر الطلب الذي تريد استرداده:',
        'refund_reason_ask': '💸 <b>طلب استرداد</b>\n\nأرسل <b>سبب</b> طلب الاسترداد:\n\nللإلغاء: /cancel',
        'refund_sent': '✅ <b>تم إرسال طلب الاسترداد!</b>\n\nسيراجعه الأدمن ويرد عليك قريباً.',
        'refund_approved': '✅ <b>تم قبول طلب استردادك!</b>\n\n💰 تم إضافة <b>{amount}</b> إلى محفظتك.',
        'refund_rejected': '❌ <b>تم رفض طلب استردادك.</b>\n\nللاستفسار تواصل مع الدعم.',

        # شام كاش وسيرياتيل
        'sham_cash_title': '💳 <b>شحن عبر شام كاش</b>',
        'sham_cash_steps': '1️⃣ افتح تطبيق شام كاش\n2️⃣ اختر "دفع"\n3️⃣ أدخل الكود: <code>{code}</code>\n4️⃣ أرسل صورة إثبات التحويل هنا',
        'sham_cash_amount_ask': '💰 كم المبلغ الذي حوّلته؟ (بالدولار)',
        'sham_cash_photo_ask': '📸 أرسل صورة إثبات التحويل:',
        'syriatel_title': '📞 <b>شحن عبر سيرياتيل كاش</b>',
        'syriatel_steps': '1️⃣ حوّل المبلغ إلى الكود: <code>{code}</code>\n2️⃣ أرسل رقم العملية هنا',
        'deposit_pending': '✅ <b>تم إرسال طلب الإيداع!</b>\n\nسيتم مراجعته وإضافة الرصيد قريباً.',
        'invalid_amount': '❌ أدخل مبلغاً صحيحاً أكبر من الصفر.',

        # القناة
        'channel_offer': '⚡ <b>عرض محدود الوقت!</b>\n\n📦 <b>{name}</b>\n💰 <s>{original}</s> ← <b>{discounted}</b>\n🔥 خصم <b>{pct}%</b>\n⏰ ينتهي خلال: <b>{hours} ساعة</b>\n\nلا تفوّت الفرصة! 👇',
        'channel_offer_ended': '⌛ انتهى عرض <b>{name}</b>\n\nتابع قناتنا لتعرف عن العروض القادمة! 🔔',
        'channel_new_product': '🆕 <b>منتج جديد!</b>\n\n📦 <b>{name}</b>\n💰 السعر: <b>{price}</b>\n\nمتوفر الآن في متجرنا 👇',
        'channel_announce': '📢 <b>إعلان</b>\n\n{text}',
        'open_store': '🛍️ المتجر',
        'buy_now_btn': '🛒 اشتر الآن',
    },

    'en': {
        # General
        'welcome': 'Welcome to <b>{name}</b>!\n\n{slogan}',
        'unknown_cmd': 'Sorry, I didn\'t understand. Please use the menu buttons.',
        'back': '⬅️ Back',
        'cancel': '❌ Cancel',
        'confirm': '✅ Confirm',
        'main_menu_btn': '🏠 Main Menu',
        'admin_only': '❌ This command is for admins only.',
        'error_generic': '❌ An error occurred. Please try again.',

        # Wallet
        'wallet_title': '💰 My Wallet',
        'wallet_balance': 'Current balance: <b>{balance}</b>',
        'wallet_choose_method': 'Choose a deposit method:',
        'wallet_insufficient': '❌ Insufficient balance. Price: {price}, Your balance: {balance}',
        'deposit_confirmed': '✅ Deposit confirmed!\n\n<b>{amount}</b> has been added to your wallet.\nCurrent balance: <b>{balance}</b>',

        # Purchase
        'buy_now': '🛒 Buy Now',
        'add_to_cart': '🛒 Add to Cart',
        'coupon_ask': 'Do you have a coupon?',
        'coupon_have': '🎟️ I have a coupon',
        'coupon_skip': '⏩ Skip',
        'enter_game_id': '🎮 Please send your Player ID:\n\n<b>Product:</b> {product}\n<b>Price:</b> {price}',
        'purchase_success': '✅ <b>Purchase successful!</b>\n\n📦 Product: {product}\n🎮 ID: <code>{game_id}</code>\n💰 Amount: {price}\n👛 Remaining balance: {balance}',
        'purchase_cancelled': '❌ Purchase cancelled.',
        'save_game_id': '💾 Save this ID for next time?',
        'save_yes': '✅ Yes',
        'save_no': '❌ No',
        'game_id_saved': '✅ ID saved!',
        'confirm_purchase_title': '⚠️ Confirm Purchase',
        'confirm_purchase_msg': 'Confirm purchase of:\n\n📦 {product}\n💰 {price}\n🎮 ID: <code>{game_id}</code>',

        # Orders
        'orders_title': '📋 <b>My Orders</b> ({count} orders)',
        'orders_empty': '📋 <b>My Orders</b>\n\nNo orders yet.',
        'order_shipped': '✅ <b>Your order has been shipped!</b>\n\n📦 Product: {product}\n🎮 ID: <code>{game_id}</code>\n\nThank you for shopping with us! 🙏',
        'status_pending': '⏳ Processing',
        'status_shipped': '✅ Shipped',
        'status_completed': '✅ Completed',
        'status_cancelled': '❌ Cancelled',
        'status_refunded': '💸 Refunded',
        'status_refund_req': '🔄 Refund Requested',

        # Coupon
        'coupon_enter': '🎟️ Send your coupon code:',
        'coupon_invalid': '❌ Invalid or expired coupon.',
        'coupon_applied': '✅ Coupon applied!\n\n💰 Discount: {discount}\n💵 Price after discount: {price}',

        # Settings
        'settings_title': '⚙️ <b>My Settings</b>',
        'settings_name': '👤 Name: <b>{name}</b>',
        'settings_balance': '💰 Balance: <b>{balance}</b>',
        'settings_currency': '💱 Currency: <b>{currency}</b>',
        'settings_rate': '📈 Exchange rate: <b>1$ = {rate} SYP</b>',
        'settings_lang': '🌍 Language: <b>{lang}</b>',
        'settings_2fa': '🔐 Two-factor auth: <b>{status}</b>',
        '2fa_on': 'Enabled ✅',
        '2fa_off': 'Disabled ❌',
        'change_language': '🌍 Change Language',
        'enable_2fa': '🔓 Enable 2FA',
        'disable_2fa': '🔒 Disable 2FA',
        'language_changed': '✅ Language changed to English',
        'two_fa_enabled': '✅ Two-factor authentication enabled\n\nYou\'ll be asked to confirm purchases over $2.',
        'two_fa_disabled': '✅ Two-factor authentication disabled',
        'currency_usd': '🇺🇸 USD Dollar',
        'currency_syp': '🇸🇾 Syrian Pound',

        # Referral
        'referral_title': '🔗 <b>Referral System</b>',
        'referral_desc': 'Share your link with friends.\nGet <b>{reward}</b> for each friend\'s first purchase!',
        'referral_link': '🔗 Your referral link:',
        'referral_stats': '📊 <b>Your Stats:</b>\n👥 Friends invited: <b>{total}</b>\n💰 Rewards earned: <b>{paid}</b> ({amount})',
        'referral_reward_msg': '🎉 <b>Referral Reward!</b>\n\nYour friend made their first purchase!\n💰 <b>{reward}</b> added to your wallet!',

        # Offers
        'offers_title': '⚡ <b>Limited Offers</b>',
        'offers_empty': '⚡ <b>Limited Offers</b>\n\nNo active offers right now.\nStay tuned for upcoming deals!',
        'offer_expires': '⏰ Expires in: <b>{hours}h {mins}m</b>',
        'flash_label': '🔥 <b>Limited offer!</b> Expires in {hours}h {mins}m',
        'shop_now': '🛒 Shop Now',

        # Support
        'support_title': '💬 <b>Customer Support</b>',
        'support_desc': 'Have a problem or question? Open a ticket and our team will respond.',
        'support_stats': '📋 Your tickets: <b>{total}</b> | Open: <b>{open}</b>',
        'new_ticket': '➕ New Ticket',
        'my_tickets': '📋 My Tickets',
        'ticket_subject_ask': '➕ <b>New Ticket</b>\n\nSend the <b>subject</b> of your issue:\n\nTo cancel: /cancel',
        'ticket_subject_short': '❌ Subject too short. Please be more descriptive:',
        'ticket_msg_ask': '📝 Subject: <b>{subject}</b>\n\nNow send the <b>details</b> of your issue:',
        'ticket_created': '✅ <b>Ticket submitted!</b>\n\nTicket #: <b>#{id}</b>\nOur team will reply shortly. 🙏',
        'ticket_reply': '💬 <b>New reply on your ticket #{id}</b>\n\n📌 {subject}\n\n🛡️ <b>Support:</b>\n{reply}',
        'ticket_closed_msg': '✅ <b>Your ticket #{id} has been closed.</b>\n\nWe hope we could help! 🙏',

        # Refund
        'refund_title': '💸 <b>Refund Request</b>',
        'refund_no_orders': '❌ No eligible orders for refund.',
        'refund_select': 'Select the order you want to refund:',
        'refund_reason_ask': '💸 <b>Refund Request</b>\n\nSend the <b>reason</b> for your refund:\n\nTo cancel: /cancel',
        'refund_sent': '✅ <b>Refund request submitted!</b>\n\nAn admin will review it shortly.',
        'refund_approved': '✅ <b>Your refund has been approved!</b>\n\n💰 <b>{amount}</b> has been added to your wallet.',
        'refund_rejected': '❌ <b>Your refund was rejected.</b>\n\nContact support for more info.',

        # Payments
        'sham_cash_title': '💳 <b>Deposit via Sham Cash</b>',
        'sham_cash_steps': '1️⃣ Open Sham Cash app\n2️⃣ Select "Pay"\n3️⃣ Enter code: <code>{code}</code>\n4️⃣ Send proof photo here',
        'sham_cash_amount_ask': '💰 How much did you transfer? (in USD)',
        'sham_cash_photo_ask': '📸 Send a proof photo of the transfer:',
        'syriatel_title': '📞 <b>Deposit via Syriatel Cash</b>',
        'syriatel_steps': '1️⃣ Transfer to code: <code>{code}</code>\n2️⃣ Send transaction number here',
        'deposit_pending': '✅ <b>Deposit request submitted!</b>\n\nIt will be reviewed and balance added shortly.',
        'invalid_amount': '❌ Please enter a valid amount greater than zero.',

        # Channel
        'channel_offer': '⚡ <b>Limited Time Offer!</b>\n\n📦 <b>{name}</b>\n💰 <s>{original}</s> ← <b>{discounted}</b>\n🔥 <b>{pct}% OFF</b>\n⏰ Expires in: <b>{hours} hours</b>\n\nDon\'t miss out! 👇',
        'channel_offer_ended': '⌛ Offer for <b>{name}</b> has ended.\n\nFollow our channel for upcoming deals! 🔔',
        'channel_new_product': '🆕 <b>New Product!</b>\n\n📦 <b>{name}</b>\n💰 Price: <b>{price}</b>\n\nNow available in our store 👇',
        'channel_announce': '📢 <b>Announcement</b>\n\n{text}',
        'open_store': '🛍️ Store',
        'buy_now_btn': '🛒 Buy Now',
    },

    'ku': {
        # گشتی
        'welcome': 'بەخێربێیت بۆ <b>{name}</b>!\n\n{slogan}',
        'unknown_cmd': 'ببورە، تێنەگەیشتم. تکایە دوگمەکانی لیستەکە بەکاربهێنە.',
        'back': '⬅️ گەڕانەوە',
        'cancel': '❌ هەڵweşاندنەوە',
        'confirm': '✅ پشتڕاستکردنەوە',
        'main_menu_btn': '🏠 پێڕستی سەرەکی',
        'admin_only': '❌ ئەم فەرمانە تەنها بۆ بەڕێوەبەرانە.',
        'error_generic': '❌ هەڵەیەک ڕوویدا. دووبارە هەوڵبدەوە.',

        # جزدان
        'wallet_title': '💰 جزدانەکەم',
        'wallet_balance': 'باڵانسی ئێستا: <b>{balance}</b>',
        'wallet_choose_method': 'شێوازی واریزکردن هەڵبژێرە:',
        'wallet_insufficient': '❌ باڵانسەکەت پێویستی نییە. نرخ: {price}، باڵانسەکەت: {balance}',
        'deposit_confirmed': '✅ واریزەکەت پشتڕاستکرایەوە!\n\n<b>{amount}</b> زیادکرا بۆ جزدانەکەت.\nباڵانسی ئێستا: <b>{balance}</b>',

        # کڕین
        'buy_now': '🛒 ئێستا بکڕە',
        'add_to_cart': '🛒 زیادبکە بۆ سەبەتە',
        'coupon_ask': 'کووپۆنت هەیە؟',
        'coupon_have': '🎟️ کووپۆنم هەیە',
        'coupon_skip': '⏩ تێپەڕبوون',
        'enter_game_id': '🎮 تکایە ناسنامەی یاریزانەکەت بنێرە:\n\n<b>بەرهەم:</b> {product}\n<b>نرخ:</b> {price}',
        'purchase_success': '✅ <b>کڕین سەرکەوتوو بوو!</b>\n\n📦 بەرهەم: {product}\n🎮 ناسنامە: <code>{game_id}</code>\n💰 بڕ: {price}\n👛 باڵانسی ماوە: {balance}',
        'purchase_cancelled': '❌ کڕین هەڵوەشایەوە.',
        'save_game_id': '💾 ئایا دەتەوێت ئەم ناسنامەیە بۆ جارێکی دیکە بهێڵیتەوە؟',
        'save_yes': '✅ بەڵێ',
        'save_no': '❌ نەخێر',
        'game_id_saved': '✅ ناسنامەکە هێڵدرایەوە!',
        'confirm_purchase_title': '⚠️ پشتڕاستکردنەوەی کڕین',
        'confirm_purchase_msg': 'پشتڕاستکردنەوەی کڕینی:\n\n📦 {product}\n💰 {price}\n🎮 ناسنامە: <code>{game_id}</code>',

        # داواکارییەکان
        'orders_title': '📋 <b>داواکارییەکانم</b> ({count})',
        'orders_empty': '📋 <b>داواکارییەکانم</b>\n\nهێشتا داواکارییەکت نییە.',
        'order_shipped': '✅ <b>داواکارییەکەت نێردرا!</b>\n\n📦 بەرهەم: {product}\n🎮 ناسنامە: <code>{game_id}</code>\n\nسوپاس بۆ کڕینەکەت! 🙏',
        'status_pending': '⏳ لە کارکردندایە',
        'status_shipped': '✅ نێردرا',
        'status_completed': '✅ تەواوبوو',
        'status_cancelled': '❌ هەڵوەشایەوە',
        'status_refunded': '💸 گەڕاندرایەوە',
        'status_refund_req': '🔄 داوای گەڕاندنەوە',

        # کووپۆن
        'coupon_enter': '🎟️ کۆدی کووپۆنەکەت بنێرە:',
        'coupon_invalid': '❌ کووپۆنەکە هەڵەیە یان بەسەرچووە.',
        'coupon_applied': '✅ کووپۆنەکە جێبەجێکرا!\n\n💰 داشکاندن: {discount}\n💵 نرخ لە دوای داشکاندن: {price}',

        # ڕێکخستنەکان
        'settings_title': '⚙️ <b>ڕێکخستنەکانم</b>',
        'settings_name': '👤 ناو: <b>{name}</b>',
        'settings_balance': '💰 باڵانس: <b>{balance}</b>',
        'settings_currency': '💱 دراو: <b>{currency}</b>',
        'settings_rate': '📈 ڕێژەی گۆڕانکاری: <b>1$ = {rate} ل.س</b>',
        'settings_lang': '🌍 زمان: <b>{lang}</b>',
        'settings_2fa': '🔐 دووپاڵنەری: <b>{status}</b>',
        '2fa_on': 'چالاکە ✅',
        '2fa_off': 'ناچالاکە ❌',
        'change_language': '🌍 گۆڕینی زمان',
        'enable_2fa': '🔓 چالاککردنی دووپاڵنەری',
        'disable_2fa': '🔒 ناچالاككردنی دووپاڵنەری',
        'language_changed': '✅ زمان گۆڕدرا بۆ کوردی',
        'two_fa_enabled': '✅ دووپاڵنەری چالاک کرا\n\nپێش هەر کڕینێکی سەروو $2 پشتڕاستکردنەوەت پێویستە.',
        'two_fa_disabled': '✅ دووپاڵنەری ناچالاک کرا',
        'currency_usd': '🇺🇸 دۆلاری ئەمریکی',
        'currency_syp': '🇸🇾 لیرەی سووری',

        # ئامرازی ئەرکی
        'referral_title': '🔗 <b>سیستەمی بانەوە</b>',
        'referral_desc': 'بەستەرەکەت لەگەڵ هاوڕێکانت هاوبەش بکە.\nبۆ یەکەم کڕینی هەر هاوڕێیەک <b>{reward}</b> وەردەگریت!',
        'referral_link': '🔗 بەستەری تایبەتەکەت:',
        'referral_stats': '📊 <b>ئامارەکانت:</b>\n👥 هاوڕێ بانکراوەکان: <b>{total}</b>\n💰 خەڵاتی وەرگیراو: <b>{paid}</b> ({amount})',
        'referral_reward_msg': '🎉 <b>خەڵاتی بانەوە!</b>\n\nهاوڕێکەت یەکەم کڕینی کرد!\n💰 <b>{reward}</b> زیادکرا بۆ جزدانەکەت!',

        # پێشکەشکردنەکان
        'offers_title': '⚡ <b>پێشکەشکردنە سنووردارەکان</b>',
        'offers_empty': '⚡ <b>پێشکەشکردنە سنووردارەکان</b>\n\nئێستا هیچ پێشکەشکردنێکی چالاک نییە.',
        'offer_expires': '⏰ کاتی کۆتایی: <b>{hours}س {mins}خ</b>',
        'flash_label': '🔥 <b>پێشکەشکردنی سنووردار!</b> کاتی کۆتایی لە {hours}س {mins}خ',
        'shop_now': '🛒 ئێستا بکڕە',

        # پشتگیری
        'support_title': '💬 <b>پشتگیری کڕیاران</b>',
        'support_desc': 'کێشەت هەیە؟ تیکێت بکرەوە تیمەکەمان وەڵامت دەداتەوە.',
        'support_stats': '📋 تیکێتەکانت: <b>{total}</b> | کراوە: <b>{open}</b>',
        'new_ticket': '➕ تیکێتی نوێ',
        'my_tickets': '📋 تیکێتەکانم',
        'ticket_subject_ask': '➕ <b>تیکێتی نوێ</b>\n\n<b>بابەتی</b> کێشەکەت بنێرە:\n\nبۆ هەڵوەشاندنەوە: /cancel',
        'ticket_subject_short': '❌ بابەتەکە کورتە. وردتر بیوتەوە:',
        'ticket_msg_ask': '📝 بابەت: <b>{subject}</b>\n\nئێستا <b>وردەکارییەکانی</b> کێشەکەت بنێرە:',
        'ticket_created': '✅ <b>تیکێتەکەت نێردرا!</b>\n\nژمارەی تیکێت: <b>#{id}</b>\nتیمەکەمان بەم زووانە وەڵامت دەداتەوە. 🙏',
        'ticket_reply': '💬 <b>وەڵامی نوێ لەسەر تیکێتەکەت #{id}</b>\n\n📌 {subject}\n\n🛡️ <b>پشتگیری:</b>\n{reply}',
        'ticket_closed_msg': '✅ <b>تیکێتەکەت #{id} داخرا.</b>\n\nهیوادارین یارمەتیمان دا! 🙏',

        # گەڕاندنەوە
        'refund_title': '💸 <b>داوای گەڕاندنەوە</b>',
        'refund_no_orders': '❌ هیچ داواکارییەکی مستەحەق نییە.',
        'refund_select': 'داواکارییەکە هەڵبژێرە:',
        'refund_reason_ask': '💸 <b>داوای گەڕاندنەوە</b>\n\n<b>هۆکاری</b> داواکارییەکەت بنێرە:\n\nبۆ هەڵوەشاندنەوە: /cancel',
        'refund_sent': '✅ <b>داوای گەڕاندنەوەت نێردرا!</b>\n\nبەڕێوەبەر دەیبینێتەوە.',
        'refund_approved': '✅ <b>داوای گەڕاندنەوەت پەسەندکرا!</b>\n\n💰 <b>{amount}</b> زیادکرا بۆ جزدانەکەت.',
        'refund_rejected': '❌ <b>داوای گەڕاندنەوەت رەتکرایەوە.</b>\n\nپەیوەندی لەگەڵ پشتگیری بکە.',

        # پارەدان
        'sham_cash_title': '💳 <b>واریزکردن لە ڕێگەی شام کاش</b>',
        'sham_cash_steps': '1️⃣ ئەپی شام کاش بکرەوە\n2️⃣ "پارەدان" هەڵبژێرە\n3️⃣ کۆدەکە داخڵبکە: <code>{code}</code>\n4️⃣ وێنەی ئەنجامدان بنێرە',
        'sham_cash_amount_ask': '💰 چەندە گواستیتەوە؟ (بە دۆلار)',
        'sham_cash_photo_ask': '📸 وێنەی ئەنجامدان بنێرە:',
        'syriatel_title': '📞 <b>واریزکردن لە ڕێگەی سیریاتێل کاش</b>',
        'syriatel_steps': '1️⃣ بڕەکە بگوازە بۆ کۆدەکە: <code>{code}</code>\n2️⃣ ژمارەی مامەڵەکە بنێرە',
        'deposit_pending': '✅ <b>داوای واریزەکەت نێردرا!</b>\n\nدەبینرێتەوە و باڵانسەکەت زیادکرا.',
        'invalid_amount': '❌ تکایە ژمارەیەکی دروست داخڵبکە.',

        # قەناڵ
        'channel_offer': '⚡ <b>پێشکەشکردنی کاتی سنووردار!</b>\n\n📦 <b>{name}</b>\n💰 <s>{original}</s> ← <b>{discounted}</b>\n🔥 داشکاندنی <b>{pct}%</b>\n⏰ کاتی کۆتایی: <b>{hours} کاتژمێر</b>\n\nفەوت مەکە! 👇',
        'channel_offer_ended': '⌛ پێشکەشکردنی <b>{name}</b> کۆتایی هات.\n\nقەناڵەکەمان شوێن بکەوە! 🔔',
        'channel_new_product': '🆕 <b>بەرهەمی نوێ!</b>\n\n📦 <b>{name}</b>\n💰 نرخ: <b>{price}</b>\n\nئێستا بەردەستە 👇',
        'channel_announce': '📢 <b>ڕاگەیاندن</b>\n\n{text}',
        'open_store': '🛍️ فرۆشگا',
        'buy_now_btn': '🛒 ئێستا بکڕە',
    }
}

def t(lang: str, key: str, **kwargs) -> str:
    """جلب نص مترجم."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS['ar']).get(key, TRANSLATIONS['ar'].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text

LANGUAGE_NAMES = {
    'ar': '🇸🇦 العربية',
    'en': '🇬🇧 English',
    'ku': '🏴 کوردی',
}
