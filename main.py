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

if not BOT_TOKEN:
    raise ValueError("توکن ربات (BOT_TOKEN) در فایل .env تعریف نشده است!")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    init_db()
    
    # اگر از پروکسی سیستم استفاده می‌کنید (مثلا V2Ray پورت HTTP یا SOCKS5)
    # پورت 10809 برای HTTP پروکسی V2Ray/v2rayN است
    session = AiohttpSession(proxy="http://127.0.0.1:10808")
    
    bot = Bot(token=str(BOT_TOKEN), session=session)
    dp = Dispatcher()
    
    dp.include_router(admin_router)
    dp.include_router(user_router)
    
    print("bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())