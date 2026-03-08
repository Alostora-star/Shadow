# start.py — يشغل البوت والـ API معاً + keep-alive
import asyncio
import threading
import os
import time
import requests

RENDER_URL = "https://shadow-3nyz.onrender.com"

def keep_alive():
    """يرسل ping كل 10 دقائق لإبقاء السيرفر مستيقظاً"""
    time.sleep(30)  # انتظر 30 ثانية بعد البدء
    while True:
        try:
            requests.get(f"{RENDER_URL}/api/health", timeout=10)
            print("✅ Keep-alive ping sent")
        except Exception as e:
            print(f"⚠️ Keep-alive failed: {e}")
        time.sleep(600)  # كل 10 دقائق

def run_api():
    """تشغيل Flask API في thread منفصل"""
    from api import app, init_sessions
    init_sessions()
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 API يعمل على المنفذ {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def run_bot():
    """تشغيل البوت مع event loop جديد"""
    from bot import main, _init
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_init())
    main()

if __name__ == "__main__":
    # Keep-alive thread
    ka_thread = threading.Thread(target=keep_alive, daemon=True)
    ka_thread.start()

    # API thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # البوت في المقدمة
    run_bot()
