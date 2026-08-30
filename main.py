import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv

from bot.database import init_db
from bot.handlers.admin import admin_router
from bot.handlers.user import user_router

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")

if not BOT_TOKEN:
    raise ValueError("توکن ربات (BOT_TOKEN) در فایل .env تعریف نشده است!")

# تبدیل صریح به str جهت اطمینان Type Checker
token_str: str = BOT_TOKEN


# وب سرور ساختگی برای پاس کردن Port Scan و نگهداری Uptime در Render
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

    # ایجاد جداول دیتابیس PostgreSQL/SQLite به‌صورت Async
    await init_db()

    if os.getenv("PORT"):
        await start_dummy_server()

    if PROXY_URL:
        session = AiohttpSession(proxy=PROXY_URL)
        bot = Bot(token=token_str, session=session)
        print(f"Bot starting with proxy: {PROXY_URL}")
    else:
        bot = Bot(token=token_str)
        print("Bot starting with direct connection (No proxy)")

    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(user_router)

    print("bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())