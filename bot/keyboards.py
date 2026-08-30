from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# منوی اصلی (Reply Keyboard)
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 خرید اشتراک"), KeyboardButton(text="👤 حساب کاربری / سرویس‌های من")],
        [KeyboardButton(text="📚 راهنما و اتصال"), KeyboardButton(text="📞 پشتیبانی")]
    ],
    resize_keyboard=True
)

# لیست پلن‌های فروش (Inline Keyboard)
plans_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚀  ماهه - 10 گیگابایت | 45,000 تومان", callback_data="buy_plan:1month_10gb:45000")],
        [InlineKeyboardButton(text="🚀  ماهه - 20 گیگابایت | 90,000 تومان", callback_data="buy_plan:1month_20gb:90000")],
        [InlineKeyboardButton(text="🚀  ماهه - 100 گیگابایت | 450,000 تومان", callback_data="buy_plan:2month_100gb:450000")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_buy")]
    ]
)

# کیبورد تایید یا رد فیش برای ادمین
def get_admin_receipt_keyboard(order_id: int, user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تایید و ارسال کانفیگ", callback_data=f"approve_order:{order_id}:{user_id}"),
                InlineKeyboardButton(text="❌ رد سفارش", callback_data=f"reject_order:{order_id}:{user_id}")
            ]
        ]
    )