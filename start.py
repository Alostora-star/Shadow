# start.py — يشغل البوت والـ API معاً
import asyncio
import threading
import os
import time
import requests

RENDER_URL = "https://shadow-3nyz.onrender.com"

def keep_alive():
    time.sleep(30)
    while True:
        try:
            requests.get(f"{RENDER_URL}/api/health", timeout=10)
            print("✅ Keep-alive ping")
        except Exception as e:
            print(f"⚠️ Keep-alive: {e}")
        time.sleep(600)

def run_api():
    from api import app
    from pg_db import init_web_tables
    init_web_tables()
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 API على المنفذ {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def run_bot():
    from bot import main, _init
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_init())
    main()

if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=run_api, daemon=True).start()
    run_bot()
