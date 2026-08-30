import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from bot.database import init_db
from bot.handlers.user import user_router
from bot.handlers.admin import admin_router

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")  # دریافت آدرس پروکسی از متغیرهای محیطی

if not BOT_TOKEN:
    raise ValueError("توکن ربات (BOT_TOKEN) در فایل .env تعریف نشده است!")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    init_db()
    
    # بررسی وجود پروکسی برای تنظیم شیء Bot
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