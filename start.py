# start.py — يشغل البوت والـ API معاً
import asyncio
import threading
import os

def run_api():
    """تشغيل Flask API في thread منفصل"""
    from api import app, init_sessions
    init_sessions()
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 API يعمل على المنفذ {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def run_bot():
    """تشغيل البوت"""
    import asyncio
    from bot import main, _init
    asyncio.get_event_loop().run_until_complete(_init())
    main()

if __name__ == "__main__":
    # تشغيل API في خلفية
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # تشغيل البوت في المقدمة
    run_bot()
