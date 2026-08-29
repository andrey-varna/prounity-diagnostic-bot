import os
from contextlib import asynccontextmanager

import models
import stripe
from aiogram.types import Update
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from sqlalchemy import select

from database import AsyncSessionLocal, Base, engine
from models import Consultation
from telegram_bot import ADMIN_TELEGRAM_ID, bot, dp


load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы в базе данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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


@app.get("/payment/success")
async def payment_success():
    return {
        "status": "success",
        "message": "Оплата успешно завершена. Подтверждаем вашу запись."
    }


@app.get("/payment/cancel")
async def payment_cancel():
    return {
        "status": "cancelled",
        "message": (
            "Оплата не была завершена. "
            "Вы можете вернуться в Telegram и попробовать снова."
        )
    }


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()

    sig_header = request.headers.get("stripe-signature")

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="Stripe webhook secret is not configured"
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid payload"
        )

    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=400,
            detail="Invalid signature"
        )

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        stripe_session_id = session["id"]

        metadata = session.get("metadata", {})

        telegram_id = metadata.get("telegram_id")
        consultation_date = metadata.get("consultation_date")
        consultation_time = metadata.get("consultation_time")

        print("=" * 50)
        print("STRIPE PAYMENT RECEIVED")
        print(f"Session ID: {stripe_session_id}")
        print(f"Telegram ID: {telegram_id}")
        print(f"Date: {consultation_date}")
        print(f"Time: {consultation_time}")
        print("=" * 50)

        # Ищем консультацию в базе
        async with AsyncSessionLocal() as db:

            result = await db.execute(
                select(Consultation).where(
                    Consultation.stripe_session_id == stripe_session_id
                )
            )

            consultation = result.scalar_one_or_none()

            if not consultation:
                print(
                    "WARNING: Consultation not found "
                    f"for Stripe session {stripe_session_id}"
                )

                return {"status": "consultation_not_found"}

            # Защита от повторной обработки Stripe webhook
            if consultation.is_processed:
                print(
                    "PAYMENT ALREADY PROCESSED "
                    f"for Stripe session {stripe_session_id}"
                )

                return {"status": "already_processed"}

            # Подтверждаем оплату
            consultation.payment_status = "paid"
            consultation.is_processed = True

            await db.commit()

        print("=" * 50)
        print("PAYMENT CONFIRMED IN DATABASE")
        print(f"Consultation ID: {consultation.id}")
        print("=" * 50)

        # Сообщение клиенту
        if telegram_id:
            try:
                await bot.send_message(
                    chat_id=int(telegram_id),
                    text=(
                        "✅ Оплата успешно получена!\n\n"
                        "Ваша консультация подтверждена.\n\n"
                        f"📅 Дата: {consultation_date}\n"
                        f"🕒 Время: {consultation_time}\n\n"
                        "Продолжительность консультации — 60 минут."
                    )
                )

            except Exception as e:
                print(
                    f"ERROR sending message to client: {e}"
                )

        # Уведомление администратору
        if ADMIN_TELEGRAM_ID:
            try:
                await bot.send_message(
                    chat_id=int(ADMIN_TELEGRAM_ID),
                    text=(
                        "💰 НОВАЯ ОПЛАТА\n\n"
                        f"📅 Дата консультации: "
                        f"{consultation_date}\n"
                        f"🕒 Время: "
                        f"{consultation_time}\n"
                        f"👤 Telegram ID клиента: "
                        f"{telegram_id}\n"
                        f"💳 Stripe Session: "
                        f"{stripe_session_id}"
                    )
                )

            except Exception as e:
                print(
                    f"ERROR sending message to admin: {e}"
                )

    return {"status": "ok"}