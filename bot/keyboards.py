from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# منوی اصلی مشتری
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 خرید کانفیگ")],
        [KeyboardButton(text="📦 سرویس‌های من"), KeyboardButton(text="📞 پشتیبانی")]
    ],
    resize_keyboard=True
)

# پلان‌های فروش
plans_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔹 ۳۰ روزه - ۵۰ گیگ (۱۵۰,۰۰۰ تومان)", callback_data="plan_50gb")],
        [InlineKeyboardButton(text="🔹 ۳۰ روزه - ۱۰۰ گیگ (۲۲۰,۰۰۰ تومان)", callback_data="plan_100gb")],
        [InlineKeyboardButton(text="🔹 ۶۰ روزه - ۲۰۰ گیگ (۳۸۰,۰۰۰ تومان)", callback_data="plan_200gb")]
    ]
)

# دکمه‌های مربوط به ادمین بر روی پیام اعلام سفارش
def admin_order_action_kb(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 ارسال کانفیگ", callback_data=f"send_config_{order_id}")]
        ]
    )