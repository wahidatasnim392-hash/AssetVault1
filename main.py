import asyncio
import logging
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os

from database import init_db
from handlers import user, admin, buy, deposit, common

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("🚀 Bot is starting...")

    # ডাটাবেজ ইনিশিয়ালাইজেশন
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # ⚠️ অত্যন্ত গুরুত্বপূর্ণ: রাউটারগুলোর সঠিক ক্রম (Common এবং User সবসময় নিচে বা ঠিকমতো থাকতে হবে)
    dp.include_router(admin.router)
    dp.include_router(deposit.router)
    dp.include_router(buy.router)
    dp.include_router(user.router)
    dp.include_router(common.router)

    # আগের জমে থাকা আপডেট বা ওয়েবহুক ক্লিয়ার করা যাতে বুট করার পর জ্যাম না থাকে
    await bot.delete_webhook(drop_pending_updates=True)
    
    logging.info("⚡ Bot Polling Started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🔴 Bot Stopped!")

        