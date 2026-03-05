# config.py
import os
import sys
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# إعدادات البوت الأساسية
BOT_TOKEN = os.getenv("BOT_TOKEN")

# التحقق من وجود التوكن
if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("❌ خطأ: لم يتم العثور على توكن البوت (BOT_TOKEN)!")
    print("يرجى التأكد من إنشاء ملف باسم .env ووضع التوكن الخاص بك فيه.")
    print("يمكنك استخدام ملف .env.example كنموذج.")
    # لا نوقف البرنامج هنا لنسمح للبوت بالتعامل مع الخطأ في Application.builder()
    # ولكننا نضع قيمة افتراضية لتجنب أخطاء NoneType في بعض الحالات
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 7524378240))
GROUP_ID = int(os.getenv("GROUP_ID", 0)) if os.getenv("GROUP_ID") else None
GROUP_JOIN_LINK = os.getenv("GROUP_JOIN_LINK")

# إعدادات المتجر (يمكن نقلها لاحقاً إلى قاعدة البيانات)
WEBSITE_NAME = "متجر الخدمات الرقمية"
WEBSITE_SLOGAN = "جودتنا تميزنا، وسرعتنا تخدمكم!"
WEBSITE_DESCRIPTION = "نقدم لكم أفضل الخدمات الرقمية بأسعار تنافسية وجودة عالية."
WEBSITE_MESSAGE = "اكتشف مجموعتنا الواسعة من الخدمات الرقمية المصممة لتلبية جميع احتياجاتك."
INSTAGRAM_USERNAME = "@ZenetsuYYY"

# إعدادات طرق الدفع
PAYMENT_METHODS = {
    "sham_cash": {
        "name": "💰 شام كاش",
        "enabled": True,
        "code": "b441bd2368ed511aebd2f9e79723936d",
        "instructions": "يرجى تحويل المبلغ باستخدام كود الاستلام"
    },
    "syriatel_cash_code": {
        "name": "🔑  سيرياتيل كاش",
        "enabled": True,
        "code": "69643514",
        "instructions": "يرجى تحويل المبلغ المطلوب باستخدام الرمز التالي"
    }
}

# اسم قاعدة البيانات
DATABASE_NAME = "bot_data.db"
