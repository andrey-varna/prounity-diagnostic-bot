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
):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",

        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "Диагностическая консультация PRO Unity Consult",
                        "description": (
                            "Персональный разбор результатов "
                            "диагностического опроса"
                        ),
                    },
                    "unit_amount": 1000,
                },
                "quantity": 1,
            }
        ],

        success_url=success_url,
        cancel_url=cancel_url,
    )

    return session