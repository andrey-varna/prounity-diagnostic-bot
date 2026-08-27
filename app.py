import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Request
from aiogram.types import Update
from telegram_bot import bot, dp
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск приложения
    me = await bot.get_me()

    print("=" * 50)
    print("BOT STARTED")
    print(f"Bot: @{me.username}")

    if WEBHOOK_URL and WEBHOOK_URL.startswith("https://"):
        await bot.set_webhook(
            url=WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True
        )

        print(f"Webhook: {WEBHOOK_URL}")
    else:
        print("Webhook: not configured (local mode)")

    print("=" * 50)

    yield

    # Остановка приложения
    await bot.delete_webhook()
    await bot.session.close()

    print("BOT STOPPED")


app = FastAPI(
    title="PRO Unity Diagnostic Bot",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "PRO Unity Diagnostic Bot"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None)
):
    if WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
            raise HTTPException(
                status_code=403,
                detail="Invalid webhook secret"
            )

    data = await request.json()

    update = Update.model_validate(
        data,
        context={"bot": bot}
    )

    await dp.feed_update(bot, update)

    return {"ok": True}