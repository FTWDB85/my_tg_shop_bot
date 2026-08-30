import os
from dotenv import load_dotenv
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards import main_menu, plans_inline, admin_order_action_kb
from bot.database import create_order, update_order_receipt, get_user_orders

# لود کردن متغیرهای محیطی
load_dotenv()

user_router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)

class OrderState(StatesGroup):
    waiting_for_receipt = State()

PLANS = {
    "plan_50gb": {"name": "۳۰ روزه / ۵۰ گیگ", "price": "۱۵۰,۰۰۰ تومان"},
    "plan_100gb": {"name": "۳۰ روزه / ۱۰۰ گیگ", "price": "۲۲۰,۰۰۰ تومان"},
    "plan_200gb": {"name": "۶۰ روزه / ۲۰۰ گیگ", "price": "۳۸۰,۰۰۰ تومان"},
}

@user_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("سلام! به فروشگاه کانفیگ خوش آمدید. از منوی زیر استفاده کنید:", reply_markup=main_menu)

@user_router.message(F.text == "🛒 خرید کانفیگ")
async def show_plans(message: Message):
    await message.answer("لطفا سرویس مورد نظر خود را انتخاب کنید:", reply_markup=plans_inline)

@user_router.callback_query(F.data.startswith("plan_"))
async def plan_selected(callback: CallbackQuery, state: FSMContext):
    if not callback.data or not callback.from_user or not callback.message:
        return

    plan_key = callback.data
    plan_info = PLANS.get(plan_key)
    
    if not plan_info:
        await callback.answer("پلن مورد نظر یافت نشد.", show_alert=True)
        return

    order_id = create_order(
        user_id=callback.from_user.id,
        username=callback.from_user.username or "ندارد",
        plan_name=plan_info["name"],
        price=plan_info["price"]
    )
    
    await state.update_data(current_order_id=order_id)
    await state.set_state(OrderState.waiting_for_receipt)
    
    text = (
        f"📦 **سفارش ثبت شد (#{order_id})**\n\n"
        f"🔹 **سرویس:** {plan_info['name']}\n"
        f"💰 **مبلغ:** {plan_info['price']}\n\n"
        f"💳 **شماره کارت جهت واریز:**\n`6037-9999-9999-9999`\n"
        f"به نام: دانیال ...\n\n"
        f"⚠️ لطفاً پس از پرداخت، تصویر فیش واریزی را همین‌جا ارسال کنید."
    )
    
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, parse_mode="Markdown")

@user_router.message(OrderState.waiting_for_receipt, F.photo)
async def process_receipt(message: Message, state: FSMContext, bot: Bot):
    if not message.photo or not message.from_user:
        return

    data = await state.get_data()
    order_id = data.get("current_order_id")
    
    if not order_id:
        await message.answer("خطا در یافتن سفارش. لطفاً دوباره از ابتدا سعی کنید.")
        await state.clear()
        return

    photo_id = message.photo[-1].file_id
    update_order_receipt(int(order_id), photo_id)
    
    await message.answer("✅ فیش شما دریافت شد. پس از بررسی توسط ادمین، کانفیگ برای شما ارسال می‌شود.")
    await state.clear()
    
# اطلاع‌رسانی به ادمین
    if ADMIN_ID != 0:
        username_str = f"@{message.from_user.username}" if message.from_user.username else "ندارد"
        admin_text = (
            f"🔔 **سفارش جدید پرداخت شده!**\n\n"
            f"🆔 **شماره سفارش:** #{order_id}\n"
            f"👤 **مشتری:** {username_str} (آیدی: `{message.from_user.id}`)\n"
        )
        try:
            await bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_id,
                caption=admin_text,
                reply_markup=admin_order_action_kb(int(order_id)),
                parse_mode="Markdown"
            )
            print(f"پیام ادمین با موفقیت به {ADMIN_ID} ارسال شد.")
        except Exception as e:
            print(f"خطا در ارسال پیام به ادمین: {e}")
    else:
        print("متغیر ADMIN_ID مقداردهی نشده است!")

@user_router.message(F.text == "📦 سرویس‌های من")
async def show_my_orders(message: Message):
    if not message.from_user:
        return

    orders = get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("شما هیچ سرویس فعالی ندارید.")
        return
    
    res = "📋 **سرویس‌های شما:**\n\n"
    for o in orders:
        res += f"🔹 **کد سفارش:** #{o[0]}\n📦 **پلن:** {o[1]}\n🔗 **لینک کانفیگ:**\n`{o[3]}`\n\n"
    await message.answer(res, parse_mode="Markdown")