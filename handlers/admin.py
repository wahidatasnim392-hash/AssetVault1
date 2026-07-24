import os
import aiosqlite
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import DB_PATH

router = Router()

def get_admin_ids():
    admin_env = os.getenv("ADMIN_ID", "")
    if not admin_env:
        return []
    return [int(aid.strip()) for aid in admin_env.split(",") if aid.strip().isdigit()]

class AdminStates(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_subcat_category_select = State()
    waiting_for_subcat_name = State()
    waiting_for_prod_name = State()
    waiting_for_prod_price = State()
    waiting_for_prod_file = State()
    waiting_for_method_name = State()
    waiting_for_method_number = State()
    waiting_for_broadcast_msg = State()
    waiting_for_ban_userid = State()

@router.message(F.text == "/admin")
@router.callback_query(F.data == "admin_panel")
async def admin_panel_handler(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    if user_id not in get_admin_ids():
        if isinstance(event, types.CallbackQuery):
            await event.answer("❌ আপনার অনুমতি নেই!", show_alert=True)
        else:
            await event.answer("❌ আপনার অনুমতি নেই!")
        return

    buttons = [
        [
            InlineKeyboardButton(text="💰 ডিপোজিট রিকোয়েস্ট", callback_data="admin_deposits"),
            InlineKeyboardButton(text="📊 পরিসংখ্যান", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="📂 ক্যাটাগরি", callback_data="admin_categories"),
            InlineKeyboardButton(text="📦 প্রোডাক্ট", callback_data="admin_products"),
            InlineKeyboardButton(text="🛍️ সাব-ক্যাট", callback_data="admin_subcategories")
        ],
        [
            InlineKeyboardButton(text="💳 পেমেন্ট মেথড ম্যানেজ", callback_data="admin_manage_methods")
        ],
        [
            InlineKeyboardButton(text="🚫 ইউজার ব্যান করুন", callback_data="admin_ban"),
            InlineKeyboardButton(text="🟢 আনব্যান করুন", callback_data="admin_unban")
        ],
        [
            InlineKeyboardButton(text="📢 ব্রডকাস্ট", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="main_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "👑 **এডমিন কন্ট্রোল প্যানেল:**\n\nনিচের অপশনগুলো থেকে সিলেক্ট করুন:"
    
    if isinstance(event, types.CallbackQuery):
        await event.answer()
        try:
            await event.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            await event.message.answer(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await event.answer(text, reply_markup=reply_markup, parse_mode="Markdown")

# --- পরিসংখ্যান (Statistics) ---
@router.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: types.CallbackQuery):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM products") as cursor:
            total_products = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM categories") as cursor:
            total_cats = (await cursor.fetchone())[0]
        async with db.execute("SELECT SUM(balance) FROM users") as cursor:
            row = await cursor.fetchone()
            total_balance = row[0] if row and row[0] else 0.0

    text = (
        f"📊 **বটের সামগ্রিক পরিসংখ্যান:**\n\n"
        f"👥 মোট ইউজার: `{total_users}` জন\n"
        f"📂 মোট ক্যাটাগরি: `{total_cats}` টি\n"
        f"📦 মোট প্রোডাক্ট আইটেম: `{total_products}` টি\n"
        f"💰 ইউজারের মোট ব্যালেন্স: `৳{total_balance}`"
    )
    buttons = [[InlineKeyboardButton(text="🔙 এডমিন প্যানেল", callback_data="admin_panel")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

# --- ক্যাটাগরি ম্যানেজমেন্ট ---
@router.callback_query(F.data == "admin_categories")
async def admin_categories_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM categories") as cursor:
            cats = await cursor.fetchall()

    buttons = []
    if cats:
        for c in cats:
            buttons.append([InlineKeyboardButton(text=f"📂 {c[1]} - ডিলিট", callback_data=f"adm_delcat_{c[0]}")])
    
    buttons.append([InlineKeyboardButton(text="➕ নতুন ক্যাটাগরি যোগ করুন", callback_data="adm_add_cat_start")])
    buttons.append([InlineKeyboardButton(text="🔙 এডমিন প্যানেল", callback_data="admin_panel")])
    await callback.message.edit_text("📂 **ক্যাটাগরি ম্যানেজমেন্ট:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data == "adm_add_cat_start")
async def adm_add_cat_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    await state.set_state(AdminStates.waiting_for_category_name)
    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_categories")]]
    await callback.message.edit_text("✍️ নতুন ক্যাটাগরির নাম লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(AdminStates.waiting_for_category_name, F.text)
async def adm_cat_name_got(message: types.Message, state: FSMContext):
    if message.from_user.id not in get_admin_ids():
        return
    cat_name = message.text.strip()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
        await db.commit()

    await state.clear()
    buttons = [[InlineKeyboardButton(text="📂 ক্যাটাগরি ম্যানেজমেন্ট", callback_data="admin_categories")]]
    await message.answer(f"✅ ক্যাটাগরি **{cat_name}** সফলভাবে তৈরি করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("adm_delcat_"))
async def adm_del_cat(callback: types.CallbackQuery):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    cat_id = int(callback.data.split("_")[2])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        await db.commit()
    buttons = [[InlineKeyboardButton(text="📂 ক্যাটাগরি ম্যানেজমেন্ট", callback_data="admin_categories")]]
    await callback.message.edit_text("🗑️ ক্যাটাগরি সফলভাবে ডিলিট করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# --- সাব-ক্যাটাগরি ম্যানেজমেন্ট ---
@router.callback_query(F.data == "admin_subcategories")
async def admin_subcategories_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT sc.id, sc.name, c.name 
            FROM vpn_subcategories sc 
            JOIN categories c ON sc.category_id = c.id
        """) as cursor:
            subcats = await cursor.fetchall()

    buttons = []
    if subcats:
        for sc in subcats:
            buttons.append([InlineKeyboardButton(text=f"📁 {sc[1]} ({sc[2]}) - ডিলিট", callback_data=f"adm_sub_del_{sc[0]}")])
    
    buttons.append([InlineKeyboardButton(text="➕ নতুন সাব-ক্যাটাগরি যোগ করুন", callback_data="adm_add_sub_start")])
    buttons.append([InlineKeyboardButton(text="🔙 এডমিন প্যানেল", callback_data="admin_panel")])
    await callback.message.edit_text("🛍️ **সাব-ক্যাটাগরি ম্যানেজমেন্ট:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data == "adm_add_sub_start")
async def adm_add_sub_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM categories") as cursor:
            cats = await cursor.fetchall()

    if not cats:
        buttons = [[InlineKeyboardButton(text="🔙 পেছনের মেনু", callback_data="admin_subcategories")]]
        await callback.message.edit_text("❌ আগে কমপক্ষে একটি ক্যাটাগরি তৈরি করুন!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    buttons = []
    for c in cats:
        buttons.append([InlineKeyboardButton(text=f"📂 {c[1]}", callback_data=f"adm_subcat_sel_{c[0]}")])
    buttons.append([InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_subcategories")])
    await callback.message.edit_text("📂 কোন ক্যাটাগরির অধীনে সাব-ক্যাটাগরি খুলবেন তা সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("adm_subcat_sel_"))
async def adm_subcat_sel(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    cat_id = int(callback.data.split("_")[3])
    await state.update_data(sub_cat_id=cat_id)
    await state.set_state(AdminStates.waiting_for_subcat_name)

    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_subcategories")]]
    await callback.message.edit_text("✍️ নতুন সাব-ক্যাটাগরির নাম লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(AdminStates.waiting_for_subcat_name, F.text)
async def adm_subcat_name_got(message: types.Message, state: FSMContext):
    if message.from_user.id not in get_admin_ids():
        return
    sub_name = message.text.strip()
    data = await state.get_data()
    cat_id = data.get("sub_cat_id")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO vpn_subcategories (category_id, name) VALUES (?, ?)", (cat_id, sub_name))
        await db.commit()

    await state.clear()
    buttons = [[InlineKeyboardButton(text="🛍️ সাব-ক্যাটাগরি ম্যানেজমেন্ট", callback_data="admin_subcategories")]]
    await message.answer(f"✅ সাব-ক্যাটাগরি **{sub_name}** সফলভাবে তৈরি করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("adm_sub_del_"))
async def adm_sub_del(callback: types.CallbackQuery):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    sub_id = int(callback.data.split("_")[3])

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM vpn_subcategories WHERE id = ?", (sub_id,))
        await db.commit()

    buttons = [[InlineKeyboardButton(text="🛍️ সাব-ক্যাটাগরি ম্যানেজমেন্ট", callback_data="admin_subcategories")]]
    await callback.message.edit_text("🗑️ সাব-ক্যাটাগরি সফলভাবে ডিলিট করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# --- প্রোডাক্ট ম্যানেজমেন্ট & যোগ করা ---
@router.callback_query(F.data == "admin_products")
async def admin_products_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name, price FROM products") as cursor:
            prods = await cursor.fetchall()

    buttons = [[InlineKeyboardButton(text="➕ নতুন প্রোডাক্ট যোগ করুন", callback_data="add_product_start")]]
    
    if prods:
        for p in prods:
            buttons.append([InlineKeyboardButton(text=f"📦 {p[1]} (৳{p[2]}) - ডিলিট", callback_data=f"adm_delprod_{p[0]}")])

    buttons.append([InlineKeyboardButton(text="🔙 এডমিন প্যানেল", callback_data="admin_panel")])
    await callback.message.edit_text("📦 **প্রোডাক্ট ম্যানেজমেন্ট:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data == "add_product_start")
async def add_product_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM categories") as cursor:
            cats = await cursor.fetchall()

    if not cats:
        buttons = [[InlineKeyboardButton(text="🔙 পেছনের মেনু", callback_data="admin_products")]]
        await callback.message.edit_text("❌ আগে কমপক্ষে একটি ক্যাটাগরি তৈরি করুন!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    buttons = []
    for c in cats:
        buttons.append([InlineKeyboardButton(text=f"📂 {c[1]}", callback_data=f"adm_pcat_{c[0]}")])
    buttons.append([InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_products")])
    await callback.message.edit_text("📦 প্রোডাক্টের জন্য ক্যাটাগরি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("adm_pcat_"))
async def adm_pcat_chosen(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    cat_id = int(callback.data.split("_")[2])
    await state.update_data(prod_cat_id=cat_id, prod_sub_id=0)

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM vpn_subcategories WHERE category_id = ?", (cat_id,)) as cursor:
            subcats = await cursor.fetchall()

    if subcats:
        buttons = []
        for sc in subcats:
            buttons.append([InlineKeyboardButton(text=f"📁 {sc[1]}", callback_data=f"adm_psub_{sc[0]}")])
        buttons.append([InlineKeyboardButton(text="⚡ সাব-ক্যাটাগরি ছাড়াই এগিয়ে যান", callback_data="adm_pnosub")])
        await callback.message.edit_text("📁 সাব-ক্যাটাগরি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
        await state.set_state(AdminStates.waiting_for_prod_name)
        buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_products")]]
        await callback.message.edit_text("📦 নতুন প্রোডাক্টের নাম লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("adm_psub_"))
async def adm_psub_chosen(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    sub_id = int(callback.data.split("_")[2])
    await state.update_data(prod_sub_id=sub_id)
    await state.set_state(AdminStates.waiting_for_prod_name)
    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_products")]]
    await callback.message.edit_text("📦 নতুন প্রোডাক্টের নাম লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data == "adm_pnosub")
async def adm_pnosub_chosen(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    await state.update_data(prod_sub_id=0)
    await state.set_state(AdminStates.waiting_for_prod_name)
    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_products")]]
    await callback.message.edit_text("📦 নতুন প্রোডাক্টের নাম লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(AdminStates.waiting_for_prod_name, F.text)
async def adm_prod_name_got(message: types.Message, state: FSMContext):
    if message.from_user.id not in get_admin_ids():
        return
    await state.update_data(prod_name=message.text.strip())
    await state.set_state(AdminStates.waiting_for_prod_price)
    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_products")]]
    await message.answer("💵 প্রোডাক্টের মূল্য সংখ্যায় লিখে পাঠান (যেমন: 150):", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(AdminStates.waiting_for_prod_price, F.text)
async def adm_prod_price_got(message: types.Message, state: FSMContext):
    if message.from_user.id not in get_admin_ids():
        return
    try:
        price = float(message.text.strip().replace(",", "."))
        if price < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ সঠিক সংখ্যায় মূল্য লিখুন:")
        return
    await state.update_data(prod_price=price)
    await state.set_state(AdminStates.waiting_for_prod_file)
    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_products")]]
    await message.answer("📄 স্টক সম্বলিত `.txt` ফাইল আপলোড করুন (প্রতি লাইনে একটি অ্যাকাউন্ট বা স্টক থাকবে):", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(AdminStates.waiting_for_prod_file, F.document)
async def adm_prod_file_got(message: types.Message, state: FSMContext):
    if message.from_user.id not in get_admin_ids():
        return
    document = message.document
    if not document.file_name.endswith('.txt'):
        await message.answer("❌ শুধু `.txt` ফাইল আপলোড করুন!")
        return

    file = await message.bot.get_file(document.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    file_content = file_bytes.read().decode("utf-8", errors="ignore").strip()

    if not file_content:
        await message.answer("❌ ফাইল খালি!")
        return

    data = await state.get_data()
    cat_id = data.get("prod_cat_id")
    sub_id = data.get("prod_sub_id", 0)
    name = data.get("prod_name")
    price = data.get("prod_price")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO products (category_id, vpn_sub_id, name, price, data) VALUES (?, ?, ?, ?, ?)",
            (int(cat_id), int(sub_id), str(name), float(price), str(file_content))
        )
        await db.commit()

    await state.clear()
    buttons = [[InlineKeyboardButton(text="📦 প্রোডাক্ট ম্যানেজমেন্ট", callback_data="admin_products")]]
    await message.answer("✅ প্রোডাক্ট এবং স্টক সফলভাবে যুক্ত হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("adm_delprod_"))
async def adm_delete_product(callback: types.CallbackQuery):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    prod_id = int(callback.data.split("_")[2])

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (prod_id,))
        await db.commit()

    buttons = [[InlineKeyboardButton(text="📦 প্রোডাক্ট ম্যানেজমেন্ট", callback_data="admin_products")]]
    await callback.message.edit_text("🗑️ প্রোডাক্ট সফলভাবে ডিলিট করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# --- ডিপোজিট রিকোয়েস্ট ম্যানেজমেন্ট ---
@router.callback_query(F.data == "admin_deposits")
async def admin_deposits_list(callback: types.CallbackQuery):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, user_id, amount, method, trx_id FROM deposits WHERE status = 'pending'") as cursor:
            deposits = await cursor.fetchall()

    if not deposits:
        buttons = [[InlineKeyboardButton(text="🔙 এডমিন প্যানেল", callback_data="admin_panel")]]
        await callback.message.edit_text("📭 কোনো পেন্ডিং ডিপোজিট রিকোয়েস্ট নেই।", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    buttons = []
    for d in deposits:
        buttons.append([
            InlineKeyboardButton(text=f"৳{d[2]} ({d[3]}) - ID: {d[1]}", callback_data=f"admdep_view_{d[0]}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 এডমিন প্যানেল", callback_data="admin_panel")])
    await callback.message.edit_text("💰 **পেন্ডিং ডিপোজিট লিস্ট:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("admdep_view_"))
async def admin_view_deposit(callback: types.CallbackQuery):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    dep_id = int(callback.data.split("_")[2])

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, user_id, amount, method, trx_id FROM deposits WHERE id = ?", (dep_id,)) as cursor:
            dep = await cursor.fetchone()

    if not dep:
        await callback.message.answer("❌ রিকোয়েস্টটি পাওয়া যায়নি!")
        return

    text = (
        f"💳 **ডিপোজিট রিকোয়েস্ট বিস্তারিত:**\n\n"
        f"🆔 ইউজার আইডি: `{dep[1]}`\n"
        f"💰 পরিমাণ: `৳{dep[2]}`\n"
        f"💸 মেথড: `{dep[3]}`\n"
        f"📝 TrxID: `{dep[4]}`"
    )
    buttons = [
        [
            InlineKeyboardButton(text="✅ অ্যাপ্রুভ (Approve)", callback_data=f"admdep_approve_{dep[0]}"),
            InlineKeyboardButton(text="❌ রিজেক্ট (Reject)", callback_data=f"admdep_reject_{dep[0]}")
        ],
        [
            InlineKeyboardButton(text="🔙 ডিপোজিট লিস্ট", callback_data="admin_deposits")
        ]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data.startswith("admdep_approve_"))
async def admin_approve_deposit(callback: types.CallbackQuery):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    dep_id = int(callback.data.split("_")[2])

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, amount FROM deposits WHERE id = ? AND status = 'pending'", (dep_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await callback.message.answer("❌ রিকোয়েস্টটি ইতিমধ্যে প্রসেস করা হয়েছে!")
                return
            user_id, amount = row[0], row[1]

        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.execute("UPDATE deposits SET status = 'approved' WHERE id = ?", (dep_id,))
        await db.commit()

        try:
            await callback.bot.send_message(user_id, f"✅ আপনার ডিপোজিট রিকোয়েস্ট সফলভাবে অনুমোদিত হয়েছে! আপনার অ্যাকাউন্টে **৳{amount}** যোগ করা হয়েছে।")
        except Exception:
            pass

    buttons = [[InlineKeyboardButton(text="💰 ডিপোজিট রিকোয়েস্ট লিস্ট", callback_data="admin_deposits")]]
    await callback.message.edit_text("✅ ডিপোজিট সফলভাবে অ্যাপ্রুভ করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("admdep_reject_"))
async def admin_reject_deposit(callback: types.CallbackQuery):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    dep_id = int(callback.data.split("_")[2])

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM deposits WHERE id = ?", (dep_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                user_id = row[0]
                try:
                    await callback.bot.send_message(user_id, "❌ আপনার ডিপোজিট রিকোয়েস্টটি এডমিন বাতিল (Reject) করেছেন।")
                except Exception:
                    pass
        await db.execute("UPDATE deposits SET status = 'rejected' WHERE id = ?", (dep_id,))
        await db.commit()

    buttons = [[InlineKeyboardButton(text="💰 ডিপোজিট রিকোয়েস্ট লিস্ট", callback_data="admin_deposits")]]
    await callback.message.edit_text("❌ ডিপোজিট রিকোয়েস্ট রিজেক্ট করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# --- পেমেন্ট মেথড ম্যানেজমেন্ট ---
@router.callback_query(F.data == "admin_manage_methods")
async def admin_manage_methods(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, method_name, account_number FROM payment_methods") as cursor:
            methods = await cursor.fetchall()

    buttons = []
    if methods:
        for m in methods:
            buttons.append([InlineKeyboardButton(text=f"🗑️ {m[1]} ({m[2]}) ডিলিট", callback_data=f"adm_delmethod_{m[0]}")])
    
    buttons.append([InlineKeyboardButton(text="➕ নতুন পেমেন্ট মেথড যোগ করুন", callback_data="adm_add_method_start")])
    buttons.append([InlineKeyboardButton(text="🔙 এডমিন প্যানেল", callback_data="admin_panel")])
    await callback.message.edit_text("💳 **পেমেন্ট মেথড ম্যানেজমেন্ট:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data == "adm_add_method_start")
async def adm_add_method_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    await state.set_state(AdminStates.waiting_for_method_name)
    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_manage_methods")]]
    await callback.message.edit_text("✍️ পেমেন্ট মেথডের নাম লিখে পাঠান (যেমন: bKash / Nagad / Rocket):", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(AdminStates.waiting_for_method_name, F.text)
async def adm_method_name_got(message: types.Message, state: FSMContext):
    if message.from_user.id not in get_admin_ids():
        return
    await state.update_data(method_name=message.text.strip())
    await state.set_state(AdminStates.waiting_for_method_number)
    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_manage_methods")]]
    await message.answer("📞 পেমেন্ট অ্যাকাউন্ট নম্বরটি লিখে পাঠান (যেমন: 017xxxxxxxx):", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(AdminStates.waiting_for_method_number, F.text)
async def adm_method_number_got(message: types.Message, state: FSMContext):
    if message.from_user.id not in get_admin_ids():
        return
    acc_num = message.text.strip()
    data = await state.get_data()
    m_name = data.get("method_name")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO payment_methods (method_name, account_number) VALUES (?, ?)", (m_name, acc_num))
        await db.commit()

    await state.clear()
    buttons = [[InlineKeyboardButton(text="💳 পেমেন্ট মেথড ম্যানেজ", callback_data="admin_manage_methods")]]
    await message.answer(f"✅ পেমেন্ট মেথড **{m_name}** ({acc_num}) সফলভাবে যোগ করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("adm_delmethod_"))
async def adm_del_method(callback: types.CallbackQuery):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    m_id = int(callback.data.split("_")[2])

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM payment_methods WHERE id = ?", (m_id,))
        await db.commit()

    buttons = [[InlineKeyboardButton(text="💳 পেমেন্ট মেথড ম্যানেজ", callback_data="admin_manage_methods")]]
    await callback.message.edit_text("🗑️ পেমেন্ট মেথড সফলভাবে ডিলিট করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# --- ইউজার ব্যান এবং আনব্যান ---
@router.callback_query(F.data == "admin_ban")
async def admin_ban_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    await state.set_state(AdminStates.waiting_for_ban_userid)
    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_panel")]]
    await callback.message.edit_text("🚫 যে ইউজারকে ব্যান করতে চান তার **User ID** লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(AdminStates.waiting_for_ban_userid, F.text)
async def admin_ban_user_got(message: types.Message, state: FSMContext):
    if message.from_user.id not in get_admin_ids():
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ সঠিক সংখ্যায় ইউজার আইডি লিখুন:")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
        await db.commit()

    await state.clear()
    buttons = [[InlineKeyboardButton(text="🔙 এডমিন প্যানেল", callback_data="admin_panel")]]
    await message.answer(f"✅ ইউজার আইডি `({target_id})` কে সফলভাবে ব্যান করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@router.callback_query(F.data == "admin_unban")
async def admin_unban_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    await state.set_state(AdminStates.waiting_for_ban_userid)
    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_panel")]]
    await callback.message.edit_text("🟢 যে ইউজারকে আনব্যান করতে চান তার **User ID** লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(AdminStates.waiting_for_ban_userid, F.text)
async def admin_unban_user_got(message: types.Message, state: FSMContext):
    if message.from_user.id not in get_admin_ids():
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ সঠিক সংখ্যায় ইউজার আইডি লিখুন:")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
        await db.commit()

    await state.clear()
    buttons = [[InlineKeyboardButton(text="🔙 এডমিন প্যানেল", callback_data="admin_panel")]]
    await message.answer(f"✅ ইউজার আইডি `({target_id})` কে সফলভাবে আনব্যান করা হয়েছে!", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

# --- ব্রডকাস্ট (Broadcast) ---
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in get_admin_ids():
        return
    await callback.answer()
    await state.set_state(AdminStates.waiting_for_broadcast_msg)
    buttons = [[InlineKeyboardButton(text="❌ বাতিল", callback_data="admin_panel")]]
    await callback.message.edit_text("📢 সমস্ত ইউজারের কাছে পাঠানোর জন্য আপনার **ব্রডকাস্ট মেসেজটি** লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.message(AdminStates.waiting_for_broadcast_msg)
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id not in get_admin_ids():
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()

    await state.clear()
    status_msg = await message.answer("⏳ ব্রডকাস্ট পাঠানো শুরু হয়েছে...")

    success_count = 0
    fail_count = 0

    for u in users:
        uid = u[0]
        try:
            await message.bot.send_message(uid, message.text, parse_mode="Markdown")
            success_count += 1
        except Exception:
            fail_count += 1

    buttons = [[InlineKeyboardButton(text="🔙 এডমিন প্যানেল", callback_data="admin_panel")]]
    await status_msg.edit_text(
        f"📢 **ব্রডকাস্ট সম্পন্ন!**\n\n"
        f"✅ সফলভাবে পাঠানো হয়েছে: `{success_count}` জনের কাছে\n"
        f"❌ ব্যর্থ হয়েছে: `{fail_count}` জনের কাছে",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )