import os
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привет!\n\n"
        "Это диагностический бот PRO Unity Consult.\n\n"
        "Сейчас мы запускаем новую систему диагностики."
    )

@router.message()
async def message_handler(message: Message):
    await message.answer(
        f"Получил ваше сообщение:\n\n{message.text}"
    )

async def notify_admin(text: str):
    if not ADMIN_TELEGRAM_ID:
        return

    await bot.send_message(
        chat_id=int(ADMIN_TELEGRAM_ID),
        text=text
    )