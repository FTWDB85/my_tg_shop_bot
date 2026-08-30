import os
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database import (
    add_or_update_user,
    create_order,
    update_order_receipt,
    get_user_orders,
    count_pending_orders
)
from bot.keyboards import main_keyboard, plans_keyboard
from bot.keyboards import admin_main_keyboard
from aiogram.fsm.context import FSMContext
from bot.keyboards import main_keyboard

user_router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

class BuyState(StatesGroup):
    waiting_for_receipt = State()

@user_router.message(F.text == "❌ انصراف")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("عملیاتی برای لغو وجود ندارد.", reply_markup=main_keyboard)
        return

    await state.clear()
    await message.answer("❌ عملیات جاری لغو شد. به منوی اصلی بازگشتید.", reply_markup=main_keyboard)
@user_router.callback_query(F.data == "cancel_order")
async def cancel_order_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("عملیات لغو شد.")
    if isinstance(callback.message, types.Message):
        await callback.message.answer("❌ سفارش لغو شد. به منوی اصلی بازگشتید.", reply_markup=main_keyboard)

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

@user_router.message(F.text == "🛒 خرید اشتراک")
async def show_plans(message: types.Message):
    await message.answer("لطفاً پلن مورد نظر خود را انتخاب کنید:", reply_markup=plans_keyboard)

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
        
        # ثبت سفارش در دیتابیس
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
        
        # فرمت قیمت
        formatted_price = f"{int(price):,}" if price.isdigit() else price

        # استفاده از فرمت HTML برای جلوگیری از خطای پارسر تلگرام
        text = (
            f"💳 <b>فاکتور پرداخت</b>\n\n"
            f"🔹 <b>پلن:</b> {plan_id}\n"
            f"🔹 <b>مبلغ:</b> {formatted_price} تومان\n\n"
            f"لطفاً مبلغ را به کارت زیر واریز کرده و <b>تصویر فیش واریزی</b> را ارسال کنید:\n\n"
            f"📌 شماره کارت:\n<code>{card_number}</code>\n"
            f"👤 به نام: {card_owner}"
        )
        await callback.message.edit_text(text, parse_mode="HTML")

    except Exception as e:
        import traceback
        print("❌ ERROR IN process_plan_selection:")
        traceback.print_exc()
        await callback.message.answer("⚠️ خطایی در ثبت فاکتور رخ داد. لطفاً دوباره تلاش کنید.")
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
    
    await message.answer("✅ فیش واریزی شما دریافت شد و برای ادمین ارسال گردید.")
    
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
            reply_markup=admin_main_keyboard,  # ارسال مستقیم کیبورد ادمین همراه با نوتیفیکیشن
            parse_mode="HTML"
        )
        except Exception as e:
           print(f"Notification error: {e}")

@user_router.message(F.text == "👤 حساب کاربری / سرویس‌های من")
async def show_account(message: types.Message):
    user = message.from_user
    if not user:
        return

    orders = await get_user_orders(user.id)
    if not orders:
        await message.answer("شما در حال حاضر هیچ سرویس فعالی ندارید.")
        return
    
    text = "📱 **سرویس‌های فعال شما:**\n\n"
    for ord in orders:
        text += f"🔹 پلن: {ord.plan_name}\n🔑 لینک اتصال:\n`{ord.config_link}`\n\n"
    await message.answer(text, parse_mode="Markdown")