import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from bot.handlers import router

load_dotenv()
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")
print(f"ADMIN_TELEGRAM_ID loaded: {ADMIN_TELEGRAM_ID}")
BOT_TOKEN = os.getenv("BOT_TOKEN")


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def notify_admin(text: str):
    if not ADMIN_TELEGRAM_ID:
        return

    await bot.send_message(
        chat_id=int(ADMIN_TELEGRAM_ID),
        text=text
    )