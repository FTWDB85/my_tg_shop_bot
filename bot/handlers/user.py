import os
from typing import Any
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database import (
    add_or_update_user,
    create_order,
    update_order_receipt,
    get_user_orders,
    count_pending_orders
)
from bot.keyboards import main_keyboard, plans_keyboard, admin_main_keyboard

user_router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

class BuyState(StatesGroup):
    waiting_for_receipt = State()

# کیبورد اینلاین انصراف زیر فاکتور
cancel_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="❌ انصراف از خرید", callback_data="cancel_order")]
    ]
)

# ---------- مدیریت انصراف (دکمه‌های متنی و اینلاین) ----------
@user_router.message(F.text.in_({"❌ انصراف", "❌ لغو", "🔙 بازگشت", "انصراف", "لغو"}))
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ عملیات جاری لغو شد. به منوی اصلی بازگشتید.", reply_markup=main_keyboard)

@user_router.callback_query(F.data == "cancel_order")
async def cancel_order_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("عملیات لغو شد.")
    if isinstance(callback.message, types.Message):
        try:
            await callback.message.edit_text("❌ فرآیند خرید لغو شد. می‌توانید از منوی اصلی استفاده کنید.")
        except Exception:
            await callback.message.answer("❌ عملیات لغو شد.", reply_markup=main_keyboard)

# ---------- دستور شروع ----------
@user_router.message(CommandStart())
async def cmd_start(message: types.Message):
    user = message.from_user
    if not user:
        return

    await add_or_update_user(
        telegram_id=user.id,
        username=user.username or "",
        full_name=user.full_name or ""
    )
    await message.answer(
        f"سلام {user.first_name} عزیز! 👋\nبه فروشگاه VPN خوش آمدید.\nلطفاً از منوی زیر گزینه مورد نظر را انتخاب کنید:",
        reply_markup=main_keyboard
    )

# ---------- نمایش پلن‌ها ----------
@user_router.message(F.text == "🛒 خرید اشتراک")
async def show_plans(message: types.Message):
    await message.answer("لطفاً پلن مورد نظر خود را انتخاب کنید:", reply_markup=plans_keyboard)

# ---------- انتخاب پلن و ایجاد فاکتور ----------
@user_router.callback_query(F.data.startswith("buy_plan:"))
async def process_plan_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    user = callback.from_user
    if not user or not callback.message or not callback.data:
        return

    if not isinstance(callback.message, types.Message):
        return

    try:
        parts = callback.data.split(":")
        if len(parts) != 3:
            return

        _, plan_id, price = parts

        order_id = await create_order(
            user_id=user.id,
            username=user.username or "",
            plan_name=plan_id,
            price=price
        )

        await state.set_state(BuyState.waiting_for_receipt)
        await state.update_data(order_id=order_id)

        card_number = os.getenv("CARD_NUMBER", "6037-9999-9999-9999")
        card_owner = os.getenv("CARD_OWNER", "نام صاحب کارت")

        formatted_price = f"{int(price):,}" if price.isdigit() else price

        text = (
            f"💳 <b>فاکتور پرداخت</b>\n\n"
            f"🔹 <b>پلن:</b> {plan_id}\n"
            f"🔹 <b>مبلغ:</b> {formatted_price} تومان\n\n"
            f"لطفاً مبلغ را به کارت زیر واریز کرده و <b>تصویر فیش واریزی</b> را ارسال کنید:\n\n"
            f"📌 شماره کارت:\n<code>{card_number}</code>\n"
            f"👤 به نام: {card_owner}"
        )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cancel_inline_keyboard)

    except Exception as e:
        import traceback
        print("❌ ERROR IN process_plan_selection:")
        traceback.print_exc()
        await callback.message.answer("⚠️ خطایی در ثبت فاکتور رخ داد. لطفاً دوباره تلاش کنید.")

# ---------- دریافت فیش واریزی ----------
@user_router.message(BuyState.waiting_for_receipt, F.photo)
async def process_receipt(message: types.Message, state: FSMContext):
    user = message.from_user
    bot = message.bot
    if not user or not message.photo or not bot:
        return

    data = await state.get_data()
    raw_order_id = data.get("order_id")

    if not raw_order_id:
        await message.answer("❌ خطایی رخ داد. لطفاً مجدداً فرآیند خرید را آغاز کنید.")
        await state.clear()
        return

    order_id: int = int(raw_order_id)
    photo_id = message.photo[-1].file_id

    await update_order_receipt(order_id=order_id, receipt_file_id=photo_id)
    await state.clear()

    await message.answer("✅ فیش واریزی شما دریافت شد و برای ادمین ارسال گردید.", reply_markup=main_keyboard)

    if ADMIN_ID != 0:
        try:
            pending_count = await count_pending_orders()
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🔔 <b>سفارش جدید ثبت شد!</b>\n\n"
                    f"تعداد سفارش‌های در انتظار پردازش: <b>{pending_count} سفارش</b>\n"
                    f"جهت بررسی، از منوی زیر روی دکمه «📥 سفارش‌های در انتظار» کلیک کنید."
                ),
                reply_markup=admin_main_keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Notification error: {e}")

# ---------- حساب کاربری و سرویس‌ها ----------
@user_router.message(F.text == "👤 حساب کاربری / سرویس‌های من")
async def show_account(message: types.Message):
    user = message.from_user
    if not user:
        return

    orders: Any = await get_user_orders(user.id)
    if not orders:
        await message.answer("شما در حال حاضر هیچ سرویس فعالی ندارید.")
        return

    text = "📱 <b>سرویس‌های شما:</b>\n\n"
    for ord_item in orders:
        if isinstance(ord_item, dict):
            p_name = ord_item.get('plan_name', '')
            c_link = ord_item.get('config_link', '')
            status = ord_item.get('status', '')
        else:
            p_name = getattr(ord_item, 'plan_name', '')
            c_link = getattr(ord_item, 'config_link', '')
            status = getattr(ord_item, 'status', '')

        if status == "completed":
            text += f"🔹 پلن: <b>{p_name}</b>\n🔑 لینک اتصال:\n<code>{c_link}</code>\n-------------------\n"
        elif status == "pending":
            text += f"🔹 پلن: <b>{p_name}</b>\n⏳ وضعیت: <i>در انتظار تایید فیش</i>\n-------------------\n"

    await message.answer(text, parse_mode="HTML")

# ---------- راهنما و نحوه اتصال ----------
@user_router.message(F.text == "📌 راهنما و نحوه اتصال")
async def show_guide(message: types.Message):
    guide_text = (
        "📚 <b>راهنمای اتصال به سرویس‌ها</b>\n\n"
        "<b>📱 اندروید:</b>\n"
        "برنامه <b>v2rayNG</b> را نصب کرده، لینک کانفیگ را کپی کنید و در برنامه دکمه <code>+</code> را زده و گزینه <b>Import clipboard</b> را انتخاب کنید.\n\n"
        "<b>🍎 آیفون (iOS):</b>\n"
        "برنامه <b>v2BOX</b> یا <b>Streisand</b> را از اپ‌استور دانلود کنید و لینک دریافتی را وارد نمائید.\n\n"
        "<b>💻 ویندوز:</b>\n"
        "از برنامه <b>v2rayN</b> استفاده کنید.\n\n"
        "❓ در صورت وجود هرگونه مشکل، می‌توانید با پشتیبانی در ارتباط باشید."
    )
    await message.answer(guide_text, parse_mode="HTML")


# ---------- پشتیبانی ----------
@user_router.message(F.text == "👨‍💻 پشتیبانی")
async def show_support(message: types.Message):
    support_text = (
        "👩‍💻 <b>پشتیبانی فنی</b>\n\n"
        "در صورت بروز هرگونه مشکل، عدم اتصال یا سوال درباره سفارش‌ها، "
        "می‌توانید با پشتیبانی در ارتباط باشید:\n\n"
        "🆔 @FTWDB1"
    )
    await message.answer(support_text, parse_mode="HTML")