import aiosqlite
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from database import DB_PATH

router = Router()

# স্থায়ী Reply Keyboard (নিচের শর্টকাট বাটনগুলো)
def get_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Buy Now"), KeyboardButton(text="Deposit")],
            [KeyboardButton(text="Profile"), KeyboardButton(text="Referral")]
        ],
        resize_keyboard=True
    )

# --- ১. /start কমান্ড ও মূল মেনু ---
@router.message(F.text == "/start")
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    # রেফারেল হ্যান্ডলিং চেক
    args = message.text.split()
    referred_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            potential_ref = int(args[1].split("_")[1])
            if potential_ref != user_id:
                referred_by = potential_ref
        except ValueError:
            pass

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, referred_by FROM users WHERE user_id = ?", (user_id,)) as cursor:
            existing_user = await cursor.fetchone()

        if not existing_user:
            await db.execute(
                "INSERT INTO users (user_id, username, balance, referred_by) VALUES (?, ?, 0.0, ?)",
                (user_id, username, referred_by)
            )
            await db.commit()

    buttons = [
        [InlineKeyboardButton(text="🛍️ প্রোডাক্ট কিনুন", callback_data="buy_product")],
        [InlineKeyboardButton(text="💳 টাকা এড করুন", callback_data="deposit_menu")],
        [InlineKeyboardButton(text="👤 প্রোফাইল / ব্যালেন্স", callback_data="profile")],
        [InlineKeyboardButton(text="📞 সাপোর্ট", callback_data="support")]
    ]
    
    text = (
        f"স্বাগতম **{full_name}** আমাদের বটটিতে! ✨\n\n"
        "নিচের অপশনগুলো থেকে আপনার প্রয়োজনীয় সেবাটি বেছে নিন:"
    )
    
    await message.answer(text, reply_markup=get_reply_keyboard(), parse_mode="Markdown")
    await message.answer("মূল মেনু:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

# --- ২. মূল মেনু কলব্যাক ---
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    
    buttons = [
        [InlineKeyboardButton(text="🛍️ প্রোডাক্ট কিনুন", callback_data="buy_product")],
        [InlineKeyboardButton(text="💳 টাকা এড করুন", callback_data="deposit_menu")],
        [InlineKeyboardButton(text="👤 প্রোফাইল / ব্যালেন্স", callback_data="profile")],
        [InlineKeyboardButton(text="📞 সাপোর্ট", callback_data="support")]
    ]
    
    await callback.message.edit_text(
        "🏠 **মূল মেনু:**\n\nনিচের অপশনগুলো থেকে আপনার পছন্দমতো অপশন সিলেক্ট করুন:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )

# --- ৩. প্রোফাইল অপশন (Inline) ---
@router.callback_query(F.data == "profile")
async def profile_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user_id = callback.from_user.id
    full_name = callback.from_user.full_name

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0.0

    text = (
        f"👤 **আপনার প্রফাইল তথ্য:**\n\n"
        f"📛 **নাম:** {full_name}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"💰 **বর্তমান ব্যালেন্স:** ৳{balance}"
    )

    buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

# --- ৪. রেফারেল অপশন (Inline) ---
@router.callback_query(F.data == "referral")
async def referral_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user_id = callback.from_user.id
    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    text = (
        f"👥 **রেফারেল প্রোগ্রাম:**\n\n"
        f"আপনার বন্ধুদের আমাদের বটটি শেয়ার করুন এবং প্রতি রেফারে বোনাস অর্জন করুন!\n\n"
        f"🔗 **আপনার রেফারেল লিংক:**\n`{ref_link}`"
    )

    buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

# --- ৫. সাপোর্ট (Inline) ---
@router.callback_query(F.data == "support")
async def support_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    
    text = (
        "📞 **সহায়তা বা সাপোর্ট:**\n\n"
        "যেকোনো সমস্যায় বা পেমেন্ট সংক্রান্ত বিষয়ে আমাদের সাথে যোগাযোগ করুন:"
    )
    buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")


# --- ৬. নিচের Reply Keyboard শর্টকাটগুলো ---

@router.message(F.text == "Buy Now")
async def reply_buy_now_shortcut(message: types.Message, state: FSMContext):
    await state.clear()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM categories") as cursor:
            cats = await cursor.fetchall()

    if not cats:
        buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
        await message.answer("❌ দুঃখিত, বর্তমানে কোনো ক্যাটাগরি উপলব্ধ নেই!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    buttons = []
    for c in cats:
        buttons.append([InlineKeyboardButton(text=f"📂 {c[1]}", callback_data=f"buycat_{c[0]}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")])
    await message.answer("🛍️ **ক্যাটাগরি নির্বাচন করুন:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")


@router.message(F.text == "Profile")
async def reply_profile_shortcut(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0.0

    text = (
        f"👤 **আপনার প্রফাইল তথ্য:**\n\n"
        f"📛 **নাম:** {full_name}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"💰 **বর্তমান ব্যালেন্স:** ৳{balance}"
    )
    buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
    await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.message(F.text == "Referral")
async def reply_referral_shortcut(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    text = (
        f"👥 **রেফারেল প্রোগ্রাম:**\n\n"
        f"আপনার বন্ধুদের আমাদের বটটি শেয়ার করুন এবং প্রতি রেফারে বোনাস অর্জন করুন!\n\n"
        f"🔗 **আপনার রেফারেল লিংক:**\n`{ref_link}`"
    )
    buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
    await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))