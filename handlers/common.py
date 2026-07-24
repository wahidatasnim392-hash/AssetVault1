import aiosqlite
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import DB_PATH

router = Router()

async def is_user_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row and row[0] == 1

@router.message(F.text == "/start")
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    if await is_user_banned(user_id):
        await message.answer("❌ আপনি এই বট থেকে ব্যানড হয়েছেন!")
        return

    # রেফারেল হ্যান্ডলিং
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != user_id:
            referrer_id = ref_id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, referred_by FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await db.execute(
                    "INSERT INTO users (user_id, balance, referred_by) VALUES (?, 0.0, ?)",
                    (user_id, referrer_id)
                )
                await db.commit()

    buttons = [
        [
            InlineKeyboardButton(text="🛍️ Buy Now", callback_data="buy_product"),
            InlineKeyboardButton(text="💳 Deposit", callback_data="deposit_menu")
        ],
        [
            InlineKeyboardButton(text="👤 Profile", callback_data="user_profile"),
            InlineKeyboardButton(text="👥 Referral", callback_data="user_referral")
        ]
    ]
    
    # এডমিন চেক করে বাটন দেওয়া
    import os
    admin_env = os.getenv("ADMIN_ID", "")
    admin_list = [int(aid.strip()) for aid in admin_env.split(",") if aid.strip().isdigit()]
    if user_id in admin_list:
        buttons.append([InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = (
        f"👋 স্বাগতম **{message.user.first_name if hasattr(message, 'user') else message.from_user.first_name}**!\n\n"
        f"আমাদের বট থেকে আপনি খুব সহজেই অটোমেটিক প্রোডাক্ট কিনতে এবং ব্যালেন্স এড করতে পারবেন।"
    )
    await message.answer(text, reply_markup=reply_markup, parse_mode="Markdown")

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user_id = callback.from_user.id

    if await is_user_banned(user_id):
        await callback.message.edit_text("❌ আপনি এই বট থেকে ব্যানড হয়েছেন!")
        return

    buttons = [
        [
            InlineKeyboardButton(text="🛍️ Buy Now", callback_data="buy_product"),
            InlineKeyboardButton(text="💳 Deposit", callback_data="deposit_menu")
        ],
        [
            InlineKeyboardButton(text="👤 Profile", callback_data="user_profile"),
            InlineKeyboardButton(text="👥 Referral", callback_data="user_referral")
        ]
    ]

    import os
    admin_env = os.getenv("ADMIN_ID", "")
    admin_list = [int(aid.strip()) for aid in admin_env.split(",") if aid.strip().isdigit()]
    if user_id in admin_list:
        buttons.append([InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("🏠 **মূল মেনু:**\n\nনিচের অপশনগুলো থেকে সিলেক্ট করুন:", reply_markup=reply_markup, parse_mode="Markdown")

@router.callback_query(F.data == "user_profile")
async def user_profile_callback(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0.0

        async with db.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,)) as cursor:
            ref_count = (await cursor.fetchone())[0]

    text = (
        f"👤 **আপনার প্রোফাইল:**\n\n"
        f"🆔 ইউজার আইডি: `{user_id}`\n"
        f"💰 ব্যালেন্স: `৳{balance}`\n"
        f"👥 মোট রেফারেল: `{ref_count}` জন"
    )
    buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data == "user_referral")
async def user_referral_callback(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,)) as cursor:
            ref_count = (await cursor.fetchone())[0]

    text = (
        f"👥 **রেফারেল প্রোগ্রাম:**\n\n"
        f"আপনার রেফারেল লিংক দিয়ে কেউ জয়েন করলে এবং কেনাকাটা করলে আপনি পাবেন **৫% কমিশন**!\n\n"
        f"🔗 আপনার লিংক:\n`{ref_link}`\n\n"
        f"📊 মোট রেফার করেছেন: **{ref_count}** জন"
    )
    buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")