import os
import aiosqlite
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import DB_PATH
from keyboards import quantity_keyboard

router = Router()

async def apply_referral_commission(buyer_id: int, spent_amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT referred_by FROM users WHERE user_id = ?", (buyer_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or not row[0]:
                return
            referrer_id = row[0]

        commission = spent_amount * 0.05
        if commission <= 0:
            return

        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?", 
            (commission, referrer_id)
        )
        await db.commit()

@router.message(F.text.in_(["Buy Now", "🛍️ Buy Now"]))
async def reply_buy_now_direct(message: types.Message, state: FSMContext):
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

@router.callback_query(F.data == "buy_product")
async def show_categories_for_buy(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM categories") as cursor:
            cats = await cursor.fetchall()

    if not cats:
        buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
        await callback.message.edit_text("❌ দুঃখিত, বর্তমানে কোনো ক্যাটাগরি উপলব্ধ নেই!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    buttons = []
    for c in cats:
        buttons.append([InlineKeyboardButton(text=f"📂 {c[1]}", callback_data=f"buycat_{c[0]}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")])
    await callback.message.edit_text("🛍️ **ক্যাটাগরি নির্বাচন করুন:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("buycat_"))
async def show_products_in_category(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    cat_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM vpn_subcategories WHERE category_id = ?", (cat_id,)) as cursor:
            subcats = await cursor.fetchall()

        async with db.execute(
            "SELECT id, name, price FROM products WHERE category_id = ? AND (vpn_sub_id = 0 OR vpn_sub_id IS NULL)", 
            (cat_id,)
        ) as cursor:
            prods = await cursor.fetchall()

    buttons = []
    if subcats:
        for sc in subcats:
            buttons.append([InlineKeyboardButton(text=f"📁 {sc[1]}", callback_data=f"buysub_{sc[0]}")])

    if prods:
        for p in prods:
            buttons.append([InlineKeyboardButton(text=f"📦 {p[1]} - ৳{p[2]}", callback_data=f"buydetails_{p[0]}")])

    if not subcats and not prods:
        buttons.append([InlineKeyboardButton(text="🔙 পেছনের ক্যাটাগরি", callback_data="buy_product")])
        await callback.message.edit_text("❌ এই ক্যাটাগরিতে বর্তমানে কোনো প্রোডাক্ট নেই!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    buttons.append([InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")])
    await callback.message.edit_text("📦 **প্রোডাক্ট বা সাব-ক্যাটাগরি সিলেক্ট করুন:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("buysub_"))
async def show_products_in_subcategory(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    sub_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name, price FROM products WHERE vpn_sub_id = ?", (sub_id,)) as cursor:
            prods = await cursor.fetchall()

    if not prods:
        buttons = [[InlineKeyboardButton(text="🔙 পেছনের ক্যাটাগরি", callback_data="buy_product")]]
        await callback.message.edit_text("❌ এই সাব-ক্যাটাগরিতে কোনো প্রোডাক্ট নেই!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    buttons = []
    for p in prods:
        buttons.append([InlineKeyboardButton(text=f"📦 {p[1]} - ৳{p[2]}", callback_data=f"buydetails_{p[0]}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")])
    await callback.message.edit_text("📦 **প্রোডাক্ট সিলেক্ট করুন:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("buydetails_"))
async def product_details_and_quantity(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    prod_id = int(callback.data.split("_")[1])

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name, price, data FROM products WHERE id = ?", (prod_id,)) as cursor:
            prod = await cursor.fetchone()

    if not prod:
        await callback.message.answer("❌ প্রোডাক্টটি পাওয়া যায়নি!")
        return

    name, price, data_str = prod[0], prod[1], prod[2]
    stock_lines = [line.strip() for line in (data_str or "").split('\n') if line.strip()]
    stock_count = len(stock_lines)

    text = (
        f"🛍️ **প্রোডাক্টের বিবরণ:**\n\n"
        f"📦 **নাম:** {name}\n"
        f"💵 **মূল্য (প্রতিটি):** ৳{price}\n"
        f"📊 **স্টক موجود:** {stock_count} টি\n\n"
        f"👇 **কতোটি কিনতে চান নিচে থেকে পরিমাণ সিলেক্ট করুন:**"
    )

    await callback.message.edit_text(text, reply_markup=quantity_keyboard(prod_id), parse_mode="Markdown")

@router.callback_query(F.data.startswith("buyqty_"))
async def process_purchase(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    parts = callback.data.split("_")
    prod_id = int(parts[1])
    qty = int(parts[2])
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_row = await cursor.fetchone()
            user_balance = user_row[0] if user_row else 0.0

        async with db.execute("SELECT name, price, data FROM products WHERE id = ?", (prod_id,)) as cursor:
            prod_row = await cursor.fetchone()

    if not prod_row:
        await callback.message.answer("❌ দুঃখিত, প্রোডাক্টটি আর পাওয়া যাচ্ছে না!")
        return

    name, price, data_str = prod_row[0], prod_row[1], prod_row[2]
    total_price = price * qty

    stock_lines = [line.strip() for line in (data_str or "").split('\n') if line.strip()]

    if len(stock_lines) < qty:
        await callback.message.answer(f"❌ পর্যাপ্ত স্টক নেই! বর্তমানে স্টক আছে: {len(stock_lines)} টি।")
        return

    if user_balance < total_price:
        await callback.message.answer(
            f"❌ **পর্যাপ্ত ব্যালেন্স নেই!**\n\n"
            f"💰 আপনার ব্যালেন্স: ৳{user_balance}\n"
            f"💵 মোট খরচ: ৳{total_price}\n\n"
            f"অনুগ্রহ করে আগে ব্যালেন্স এড (Deposit) করুন।"
        )
        return

    given_items = stock_lines[:qty]
    remaining_items = stock_lines[qty:]
    new_data_str = '\n'.join(remaining_items)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (total_price, user_id))
        
        if new_data_str:
            await db.execute("UPDATE products SET data = ? WHERE id = ?", (new_data_str, prod_id))
        else:
            await db.execute("DELETE FROM products WHERE id = ?", (prod_id,))
            
            admin_env = os.getenv("ADMIN_ID", "")
            admin_list = [int(aid.strip()) for aid in admin_env.split(",") if aid.strip().isdigit()]
            
            out_of_stock_text = (
                f"⚠️ **সতর্কবার্তা: স্টক আউট (Out of Stock)!**\n\n"
                f"📦 প্রোডাক্ট: **{name}** (ID: `{prod_id}`) এর সমস্ত স্টক শেষ হয়ে গেছে এবং এটি লিস্ট থেকে রিমুভ করা হয়েছে।"
            )
            
            for admin_id in admin_list:
                try:
                    await callback.bot.send_message(admin_id, out_of_stock_text, parse_mode="Markdown")
                except Exception:
                    pass

        await db.commit()

    await apply_referral_commission(buyer_id=user_id, spent_amount=total_price)

    items_text = '\n'.join(given_items)
    success_text = (
        f"✅ **ক্রয় সফল হয়েছে! 🎉**\n\n"
        f"📦 **প্রোডাক্ট:** {name}\n"
        f"🔢 **পরিমাণ:** {qty} টি\n"
        f"💵 **মোট কাটা হয়েছে:** ৳{total_price}\n\n"
        f"🔑 **আপনার অ্যাকাউন্ট/কোডসমূহ নিচে দেওয়া হলো:**\n"
        f"```\n{items_text}\n```"
    )

    buttons = [[InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")]]
    await callback.message.edit_text(success_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")