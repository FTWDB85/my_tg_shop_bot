from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.database import get_order, set_order_completed

admin_router = Router()

class AdminState(StatesGroup):
    waiting_for_config = State()

@admin_router.callback_query(F.data.startswith("send_config_"))
async def start_send_config(callback: CallbackQuery, state: FSMContext):
    if not callback.data or not callback.message:
        return

    order_id = int(callback.data.split("_")[2])
    
    await state.update_data(target_order_id=order_id)
    await state.set_state(AdminState.waiting_for_config)
    
    if isinstance(callback.message, Message):
        await callback.message.reply(f"✏️ لطفاً **لینک کانفیگ** مربوط به سفارش #{order_id} را ارسال کنید:")
    
    await callback.answer()

@admin_router.message(AdminState.waiting_for_config, F.text)
async def process_config_link(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        return

    config_link = message.text.strip()
    data = await state.get_data()
    order_id_raw = data.get("target_order_id")
    
    if not order_id_raw:
        await message.answer("خطا در یافتن سفارش.")
        await state.clear()
        return

    order_id = int(order_id_raw)
    order = get_order(order_id)
    
    if not order:
        await message.answer("سفارش یافت نشد.")
        await state.clear()
        return
        
    user_id = int(order[1])
    plan_name = str(order[3])
    
    # به‌روزرسانی دیتابیس
    set_order_completed(order_id, config_link)
    
    # ارسال کانفیگ به مشتری
    user_msg = (
        f"✅ **سفارش شما آماده شد!**\n\n"
        f"📦 **سرویس:** {plan_name}\n"
        f"🆔 **کد سفارش:** #{order_id}\n\n"
        f"🔗 **لینک اتصال:**\n`{config_link}`\n\n"
        f"⚠️ لطفاً این لینک را در اختیار دیگران قرار ندهید."
    )
    
    try:
        await bot.send_message(chat_id=user_id, text=user_msg, parse_mode="Markdown")
        await message.answer(f"🟢 سفارش #{order_id} با موفقیت تکمیل شد و لینک برای کاربر ارسال گردید.")
    except Exception as e:
        await message.answer(f"⚠️ دیتابیس به‌روز شد، اما پیام به کاربر ارسال نشد: {e}")
        
    await state.clear()