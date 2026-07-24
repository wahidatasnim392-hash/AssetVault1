import os
import aiosqlite
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import DB_PATH

router = Router()

class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_trxid = State()

@router.message(F.text.in_(["Deposit", "💳 Deposit", "Balance", "💰 Balance", "টাকা এড করুন"]))
async def deposit_menu_message(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0.0

    buttons = [
        [InlineKeyboardButton(text="➕ ব্যালেন্স এড করুন (Deposit)", callback_data="start_deposit")],
        [InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]
    ]
    
    text = (
        f"👤 **আপনার প্রোফাইল & ব্যালেন্স:**\n\n"
        f"🆔 ইউজার আইডি: `{user_id}`\n"
        f"💰 বর্তমান ব্যালেন্স: ৳{balance}\n\n"
        f"ডিপোজিট করতে নিচের বাটনে ক্লিক করুন:"
    )
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data == "deposit_menu")
async def deposit_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0.0

    buttons = [
        [InlineKeyboardButton(text="➕ ব্যালেন্স এড করুন (Deposit)", callback_data="start_deposit")],
        [InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]
    ]
    
    text = (
        f"👤 **আপনার প্রোফাইল & ব্যালেন্স:**\n\n"
        f"🆔 ইউজার আইডি: `{user_id}`\n"
        f"💰 বর্তমান ব্যালেন্স: ৳{balance}\n\n"
        f"ডিপোজিট করতে নিচের বাটনে ক্লিক করুন:"
    )
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data == "start_deposit")
async def start_deposit_process(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, method_name, account_number FROM payment_methods") as cursor:
            methods = await cursor.fetchall()

    if not methods:
        buttons = [[InlineKeyboardButton(text="🔙 পেছনের মেনু", callback_data="deposit_menu")]]
        await callback.message.edit_text("❌ বর্তমানে কোনো পেমেন্ট মেথড যোগ করা হয়নি!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    buttons = []
    for m in methods:
        buttons.append([InlineKeyboardButton(text=f"💸 {m[1]} ({m[2]})", callback_data=f"depmethod_{m[1]}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 বাতিল", callback_data="deposit_menu")])
    await callback.message.edit_text("💳 **পেমেন্ট মেথড নির্বাচন করুন:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("depmethod_"))
async def deposit_method_chosen(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    chosen_method_name = callback.data.split("_", 1)[1]

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT method_name, account_number FROM payment_methods WHERE method_name = ?", (chosen_method_name,)) as cursor:
            method = await cursor.fetchone()

    if not method:
        await callback.message.answer("❌ পেমেন্ট মেথড পাওয়া যায়নি!")
        return

    await state.update_data(dep_method=method[0], dep_account=method[1])
    await state.set_state(DepositStates.waiting_for_amount)

    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="deposit_menu")]]
    text = (
        f"📌 নির্বাচিত মেথড: **{method[0]}**\n"
        f"📞 সেন্ড মানি নম্বর: `{method[1]}`\n\n"
        f"⚠️ আপনি এই নম্বরে যত টাকা ক্যাশআউট/সেন্ড মানি করেছেন, সেই **টাকার পরিমাণ (Amount)** শুধু সংখ্যায় লিখে পাঠান (যেমন: 100):"
    )
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.message(DepositStates.waiting_for_amount)
async def deposit_amount_got(message: types.Message, state: FSMContext):
    text_val = message.text.strip() if message.text else ""
    try:
        amount = float(text_val.replace(",", "."))
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ সঠিক সংখ্যায় টাকার পরিমাণ লিখুন (যেমন: 50 বা 500):")
        return

    await state.update_data(dep_amount=amount)
    await state.set_state(DepositStates.waiting_for_trxid)

    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="deposit_menu")]]
    await message.answer("📝 আপনার পেমেন্টের **TrxID** বা Transaction ID লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(DepositStates.waiting_for_trxid)
async def deposit_trxid_got(message: types.Message, state: FSMContext):
    trx_id = message.text.strip() if message.text else ""
    if not trx_id:
        await message.answer("❌ সঠিক TrxID লিখে পাঠান:")
        return

    data = await state.get_data()
    method = data.get("dep_method")
    amount = data.get("dep_amount")
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    full_name = message.from_user.full_name

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO deposits (user_id, amount, method, trx_id, status) VALUES (?, ?, ?, ?, 'pending')",
            (user_id, amount, method, trx_id)
        )
        dep_id = cursor.lastrowid
        await db.commit()

    await state.clear()
    
    admin_env = os.getenv("ADMIN_ID", "")
    admin_list = [int(aid.strip()) for aid in admin_env.split(",") if aid.strip().isdigit()]
    
    admin_text = (
        f"🔔 **নতুন ডিপোজিট রিকোয়েস্ট এসেছে!**\n\n"
        f"👤 ইউজার: {full_name} (@{username})\n"
        f"🆔 আইডি: `{user_id}`\n"
        f"💰 পরিমাণ: `৳{amount}`\n"
        f"💸 মেথড: `{method}`\n"
        f"📝 TrxID: `{trx_id}`"
    )
    admin_buttons = [[InlineKeyboardButton(text="🔍 চেক ও অনুমোদন করুন", callback_data=f"admdep_view_{dep_id}")]]
    
    for admin_id in admin_list:
        try:
            await message.bot.send_message(
                admin_id, 
                admin_text, 
                reply_markup=InlineKeyboardMarkup(inline_keyboard=admin_buttons), 
                parse_mode="Markdown"
            )
        except Exception:
            pass

    buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
    await message.answer("✅ আপনার ডিপোজিট রিকোয়েস্ট সফলভাবে এডমিন বরাবর পাঠানো হয়েছে! এডমিন চেক করে ব্যালেন্স যোগ করে দেবেন।", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))