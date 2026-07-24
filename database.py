import aiosqlite

DB_PATH = "database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 0.0,
                referred_by INTEGER DEFAULT NULL,
                is_banned INTEGER DEFAULT 0
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS vpn_subcategories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                vpn_sub_id INTEGER DEFAULT 0,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                data TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                method TEXT,
                trx_id TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_name TEXT,
                account_number TEXT
            )
        """)
        
        # সেফটি মাইগ্রেশন কলাম চেক
        try:
            await db.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL")
        except Exception:
            pass

        try:
            await db.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
        except Exception:
            pass

        try:
            await db.execute("ALTER TABLE products ADD COLUMN vpn_sub_id INTEGER DEFAULT 0")
        except Exception:
            pass

        await db.commit()