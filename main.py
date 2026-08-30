import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import web

from bot.database import init_db
from bot.handlers.user import user_router
from bot.handlers.admin import admin_router

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")

if not BOT_TOKEN:
    raise ValueError("توکن ربات (BOT_TOKEN) در فایل .env تعریف نشده است!")

# وب سرور ساختگی برای پاس کردن Port Scan در Render
async def handle_ping(request):
    return web.Response(text="Bot is live!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Dummy web server running on port {port}")

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    
    # اگر پورت توسط Render ارسال شده باشد، یعنی روی رندر هستیم -> وب سرور ساختگی را روشن کن
    if os.getenv("PORT"):
        await start_dummy_server()

    if PROXY_URL:
        session = AiohttpSession(proxy=PROXY_URL)
        bot = Bot(token=str(BOT_TOKEN), session=session)
        print(f"Bot starting with proxy: {PROXY_URL}")
    else:
        bot = Bot(token=str(BOT_TOKEN))
        print("Bot starting with direct connection (No proxy)")

    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(user_router)
    
    print("bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())