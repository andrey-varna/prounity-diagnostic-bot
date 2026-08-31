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
        print("=" * 50)
        print("STRIPE PAYMENT RECEIVED")
        print(f"Session ID: {stripe_session_id}")
        print(f"Telegram ID: {telegram_id}")
        print("=" * 50)
        # ====================================================
        # ИЩЕМ КОНСУЛЬТАЦИЮ И ПОДТВЕРЖДАЕМ ОПЛАТУ
        # ====================================================
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Consultation).where(
                    Consultation.stripe_session_id
                    == stripe_session_id
                )
            )
            consultation = result.scalar_one_or_none()
            if not consultation:
                print(
                    "WARNING: Consultation not found "
                    f"for Stripe session {stripe_session_id}"
                )
                return {
                    "status": "consultation_not_found"
                }
            # Защита от повторной обработки webhook
            if consultation.is_processed:
                print(
                    "PAYMENT ALREADY PROCESSED "
                    f"for Stripe session {stripe_session_id}"
                )
                return {
                    "status": "already_processed"
                }
            # Подтверждаем оплату
            consultation.payment_status = "paid"
            consultation.is_processed = True
            await db.commit()
            # Сохраняем данные до закрытия сессии БД
            consultation_id = consultation.id
            client_telegram_id = consultation.telegram_id
            goal = consultation.goal
            s = consultation.s
            o = consultation.o
            l = consultation.l
            n = consultation.n
            f = consultation.f
            h = consultation.h
            diagnostic_result = (
                consultation.diagnostic_result
            )
            desired_result = (
                consultation.desired_result
            )
            consultation_date = (
                consultation.consultation_date
            )
            consultation_time = (
                consultation.consultation_time
            )
        print("=" * 50)
        print("PAYMENT CONFIRMED IN DATABASE")
        print(f"Consultation ID: {consultation_id}")
        print("=" * 50)
        # ====================================================
        # СООБЩЕНИЕ КЛИЕНТУ
        # ====================================================
        try:
            await bot.send_message(
                chat_id=int(client_telegram_id),
                text=(
                    "✅ Оплата успешно получена!\n\n"
                    "Ваша консультация подтверждена.\n\n"
                    f"📅 Дата: {consultation_date}\n"
                    f"🕒 Время: {consultation_time}\n\n"
                    "Продолжительность консультации — "
                    "60 минут.\n\n"
                    "До встречи!"
                )
            )
        except Exception as e:
            print(
                f"ERROR sending message to client: {e}"
            )
        # ====================================================
        # ПОЛНОЕ УВЕДОМЛЕНИЕ АДМИНИСТРАТОРУ
        # ====================================================
        if ADMIN_TELEGRAM_ID:
            try:
                admin_message = (
                    "💰 НОВАЯ ПОДТВЕРЖДЁННАЯ "
                    "КОНСУЛЬТАЦИЯ\n"
                    "════════════════════\n\n"
                    "👤 КЛИЕНТ\n"
                    f"Telegram ID: {client_telegram_id}\n\n"
                    "🎯 ЦЕЛЬ\n"
                    f"{goal or 'Не указана'}\n\n"
                    "📊 ДИАГНОСТИКА\n\n"
                    f"S — Сила: {s}\n"
                    f"O — Поддержка: {o}\n"
                    f"L — Возможности и рычаги: {l}\n\n"
                    f"N — Ограничивающие убеждения: {n}\n"
                    f"F — Страхи: {f}\n"
                    f"H — Привычки: {h}\n\n"
                    "🔢 РЕЗУЛЬТАТ ПО ФОРМУЛЕ\n"
                    f"{diagnostic_result}\n\n"
                    "✨ ЖЕЛАЕМЫЙ РЕЗУЛЬТАТ\n"
                    f"{desired_result or 'Не указан'}\n\n"
                    "📅 КОНСУЛЬТАЦИЯ\n"
                    f"Дата: {consultation_date}\n"
                    f"Время: {consultation_time}\n\n"
                    "💳 ОПЛАТА\n"
                    "Статус: ✅ ПОЛУЧЕНА\n\n"
                    "────────────────────\n"
                    f"Consultation ID: {consultation_id}\n"
                    f"Stripe Session: {stripe_session_id}"
                )
                await bot.send_message(
                    chat_id=int(ADMIN_TELEGRAM_ID),
                    text=admin_message
                )
            except Exception as e:
                print(
                    f"ERROR sending message to admin: {e}"
                )
    return {"status": "ok"}