import os
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database import (
    get_next_pending_order,
    get_recent_completed_orders,
    get_order,
    set_order_completed
)
from bot.keyboards import admin_main_keyboard, get_order_process_keyboard, main_keyboard

admin_router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

class AdminProcessState(StatesGroup):
    waiting_for_config_link = State()

@admin_router.message(Command("admin"))
async def open_admin_panel(message: types.Message):
    if not message.from_user or message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠 به پنل مدیریت خوش آمدید:", reply_markup=admin_main_keyboard)

@admin_router.message(F.text == "🔙 بازگشت به منوی کاربر")
async def back_to_user_menu(message: types.Message):
    await message.answer("به منوی اصلی بازگشتید.", reply_markup=main_keyboard)

@admin_router.message(F.text == "📥 سفارش‌های در انتظار")
async def show_pending_orders(message: types.Message):
    if not message.from_user or message.from_user.id != ADMIN_ID or not message.bot:
        return

    order = await get_next_pending_order()
    if not order:
        await message.answer("🎉 هیچ سفارشی در صف انتظار وجود ندارد!")
        return

    caption = (
        f"📥 **سفارش در انتظار پردازش #{order.id}**\n\n"
        f"👤 کاربر: @{order.username}\n"
        f"🆔 شناسه کاربر: `{order.user_id}`\n"
        f"📦 پلن انتخاب‌شده: **{order.plan_name}**\n"
        f"💰 مبلغ: **{int(order.price):,} تومان**"
    )

    if order.receipt_file_id:
        await message.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=order.receipt_file_id,
            caption=caption,
            reply_markup=get_order_process_keyboard(order.id),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            caption,
            reply_markup=get_order_process_keyboard(order.id),
            parse_mode="Markdown"
        )

@admin_router.callback_query(F.data.startswith("process_send_config:"))
async def start_send_config(callback: types.CallbackQuery, state: FSMContext):
    if not callback.from_user or callback.from_user.id != ADMIN_ID or not callback.data:
        return

    order_id = int(callback.data.split(":")[1])
    order = await get_order(order_id)

    if not order or order.status == "completed":
        await callback.answer("⚠️ برای این سفارش قبلاً کانفیگ ارسال شده است!", show_alert=True)
        if isinstance(callback.message, types.Message):
            await callback.message.edit_reply_markup(reply_markup=None)
        return

    await state.update_data(current_order_id=order_id, target_user_id=order.user_id)
    await state.set_state(AdminProcessState.waiting_for_config_link)

    if isinstance(callback.message, types.Message):
        await callback.message.answer(
            f"⏳ در حال ارسال کانفیگ برای سفارش #{order_id}.\n"
            f"لطفاً **لینک کانفیگ VPN** را ارسال کنید:"
        )
    await callback.answer()

@admin_router.message(AdminProcessState.waiting_for_config_link, F.text)
async def process_and_deliver_config(message: types.Message, state: FSMContext):
    if not message.from_user or message.from_user.id != ADMIN_ID or not message.bot or not message.text:
        return

    data = await state.get_data()
    order_id = int(data.get("current_order_id", 0))
    user_id = int(data.get("target_user_id", 0))
    config_link = message.text.strip()

    await set_order_completed(order_id=order_id, config_link=config_link)
    await state.clear()

    try:
        user_msg = (
            f"🎉 **سفارش #{order_id} شما تایید شد!**\n\n"
            f"🔑 **لینک اتصال:**\n`{config_link}`"
        )
        await message.bot.send_message(chat_id=user_id, text=user_msg, parse_mode="Markdown")
        await message.reply(f"✅ کانفیگ با موفقیت برای سفارش #{order_id} ارسال شد.")
    except Exception as e:
        await message.reply(f"⚠️ کانفیگ در دیتابیس ثبت شد اما ارسال به کاربر با خطا مواجه شد: {e}")

@admin_router.message(F.text == "✅ سفارش‌های تایید شده")
async def show_completed_orders(message: types.Message):
    if not message.from_user or message.from_user.id != ADMIN_ID:
        return

    orders = await get_recent_completed_orders()
    if not orders:
        await message.answer("هیچ سفارش تایید شده‌ای ثبت نشده است.")
        return

    text = "✅ **آخرین سفارش‌های انجام شده:**\n\n"
    for ord in orders:
        text += f"🔹 **سفارش #{ord.id}** | کاربر: `{ord.user_id}`\n📦 پلن: {ord.plan_name}\n🔑 کانفیگ: `{ord.config_link}`\n---------------\n"

    await message.answer(text, parse_mode="Markdown")