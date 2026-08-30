from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# منوی اصلی کاربر
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 خرید اشتراک"), KeyboardButton(text="👤 حساب کاربری / سرویس‌های من")],
        [KeyboardButton(text="📚 راهنما و اتصال"), KeyboardButton(text="📞 پشتیبانی")]
    ],
    resize_keyboard=True
)

# لیست پلن‌های فروش
plans_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ۱ ماهه - 10 گیگابایت | 45,000 تومان", callback_data="buy_plan:1month_10gb:45000")],
        [InlineKeyboardButton(text="🚀 ۱ ماهه - 20 گیگابایت | 90,000 تومان", callback_data="buy_plan:1month_20gb:90000")],
        [InlineKeyboardButton(text="🚀 ۲ ماهه - 100 گیگابایت | 350,000 تومان", callback_data="buy_plan:2month_100gb:350000")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_order")]
    ]
)

# منوی اصلی ادمین
admin_main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 سفارش‌های در انتظار"), KeyboardButton(text="✅ سفارش‌های تایید شده")],
        [KeyboardButton(text="🔙 بازگشت به منوی کاربر")]
    ],
    resize_keyboard=True
)

# کیبورد عملیاتی هر سفارش در صف ادمین
def get_order_process_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ ارسال کانفیگ",
                    callback_data=f"process_send_config:{order_id}"
                ),
                InlineKeyboardButton(
                    text="❌ رد سفارش",
                    callback_data=f"process_reject:{order_id}"
                )
            ]
        ]
    )