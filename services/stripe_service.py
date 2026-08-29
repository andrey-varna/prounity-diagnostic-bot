import os
import stripe
from dotenv import load_dotenv

load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SECRET_KEY is not set")

stripe.api_key = STRIPE_SECRET_KEY

async def create_checkout_session(
    success_url: str,
    cancel_url: str,
    telegram_id: int,
    consultation_date: str,
    consultation_time: str,
):
    price_id = os.getenv("STRIPE_PRICE_ID")

    if not price_id:
        raise RuntimeError("STRIPE_PRICE_ID is not set")

    session = stripe.checkout.Session.create(
        mode="payment",

        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],

        success_url=success_url,
        cancel_url=cancel_url,

        metadata={
            "telegram_id": str(telegram_id),
            "consultation_date": consultation_date,
            "consultation_time": consultation_time,
        }
    )

    return session