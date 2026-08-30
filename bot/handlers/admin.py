import os
from typing import Dict, Any
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

    try:
        order: Any = await get_next_pending_order()
        if not order:
            await message.answer("🎉 هیچ سفارشی در صف انتظار وجود ندارد!")
            return

        # استخراج ایمن داده‌ها فارغ از اینکه خروجی Dict است یا مدل دیتابیس
        if isinstance(order, dict):
            order_id = int(order.get('id', 0))
            username = str(order.get('username', ''))
            user_id = int(order.get('user_id', 0))
            plan_name = str(order.get('plan_name', ''))
            price_val = order.get('price', 0)
            receipt_file_id = order.get('receipt_file_id')
        else:
            order_id = int(getattr(order, 'id', 0))
            username = str(getattr(order, 'username', ''))
            user_id = int(getattr(order, 'user_id', 0))
            plan_name = str(getattr(order, 'plan_name', ''))
            price_val = getattr(order, 'price', 0)
            receipt_file_id = getattr(order, 'receipt_file_id', None)

        formatted_price = f"{int(price_val):,}" if str(price_val).isdigit() else str(price_val)

        caption = (
            f"📥 <b>سفارش در انتظار پردازش #{order_id}</b>\n\n"
            f"👤 کاربر: @{username}\n"
            f"🆔 شناسه کاربر: <code>{user_id}</code>\n"
            f"📦 پلن انتخاب‌شده: <b>{plan_name}</b>\n"
            f"💰 مبلغ: <b>{formatted_price} تومان</b>"
        )

        if receipt_file_id:
            await message.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=str(receipt_file_id),
                caption=caption,
                reply_markup=get_order_process_keyboard(order_id),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                caption,
                reply_markup=get_order_process_keyboard(order_id),
                parse_mode="HTML"
            )
    except Exception as e:
        import traceback
        print("❌ ERROR IN show_pending_orders:")
        traceback.print_exc()
        await message.answer(f"⚠️ خطایی در نمایش سفارش رخ داد: {e}")

@admin_router.callback_query(F.data.startswith("process_send_config:"))
async def start_send_config(callback: types.CallbackQuery, state: FSMContext):
    if not callback.from_user or callback.from_user.id != ADMIN_ID or not callback.data:
        return

    try:
        order_id = int(callback.data.split(":")[1])
        order: Any = await get_order(order_id)

        if not order:
            await callback.answer("⚠️ سفارش یافت نشد!", show_alert=True)
            return

        if isinstance(order, dict):
            status = order.get('status')
            user_id = int(order.get('user_id', 0))
        else:
            status = getattr(order, 'status', None)
            user_id = int(getattr(order, 'user_id', 0))

        if status == "completed":
            await callback.answer("⚠️ برای این سفارش قبلاً کانفیگ ارسال شده است!", show_alert=True)
            if isinstance(callback.message, types.Message):
                await callback.message.edit_reply_markup(reply_markup=None)
            return

        await state.update_data(current_order_id=order_id, target_user_id=user_id)
        await state.set_state(AdminProcessState.waiting_for_config_link)

        if isinstance(callback.message, types.Message):
            await callback.message.answer(
                f"⏳ در حال ارسال کانفیگ برای سفارش #{order_id}.\n"
                f"لطفاً <b>لینک کانفیگ VPN</b> را ارسال کنید:",
                parse_mode="HTML"
            )
        await callback.answer()
    except Exception as e:
        print(f"Error in start_send_config: {e}")
        await callback.answer("⚠️ خطایی رخ داد.", show_alert=True)

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
            f"🎉 <b>سفارش #{order_id} شما تایید شد!</b>\n\n"
            f"🔑 <b>لینک اتصال:</b>\n<code>{config_link}</code>"
        )
        await message.bot.send_message(chat_id=user_id, text=user_msg, parse_mode="HTML")
        await message.reply(f"✅ کانفیگ با موفقیت برای سفارش #{order_id} ارسال شد.")
    except Exception as e:
        await message.reply(f"⚠️ کانفیگ در دیتابیس ثبت شد اما ارسال به کاربر با خطا مواجه شد: {e}")

@admin_router.message(F.text == "✅ سفارش‌های تایید شده")
async def show_completed_orders(message: types.Message):
    if not message.from_user or message.from_user.id != ADMIN_ID:
        return

    try:
        orders: Any = await get_recent_completed_orders()
        if not orders:
            await message.answer("هیچ سفارش تایید شده‌ای ثبت نشده است.")
            return

        text = "✅ <b>آخرین سفارش‌های انجام شده:</b>\n\n"
        for ord_item in orders:
            if isinstance(ord_item, dict):
                ord_id = ord_item.get('id', 0)
                u_id = ord_item.get('user_id', 0)
                p_name = ord_item.get('plan_name', '')
                c_link = ord_item.get('config_link', '')
            else:
                ord_id = getattr(ord_item, 'id', 0)
                u_id = getattr(ord_item, 'user_id', 0)
                p_name = getattr(ord_item, 'plan_name', '')
                c_link = getattr(ord_item, 'config_link', '')

            text += f"🔹 <b>سفارش #{ord_id}</b> | کاربر: <code>{u_id}</code>\n📦 پلن: {p_name}\n🔑 کانفیگ: <code>{c_link}</code>\n---------------\n"

        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        print(f"Error in show_completed_orders: {e}")
        await message.answer("⚠️ خطایی در دریافت سفارش‌های تایید شده رخ داد.")