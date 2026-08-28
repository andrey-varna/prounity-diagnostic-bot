from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import date

def rating_keyboard(min_value: int, max_value: int) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру с оценками.

    Например:
    rating_keyboard(0, 10)
    rating_keyboard(1, 10)
    """

    buttons = []

    for value in range(min_value, max_value + 1):
        buttons.append(
            InlineKeyboardButton(
                text=str(value),
                callback_data=f"rating:{value}"
            )
        )

    # По 4 кнопки в строке
    rows = [
        buttons[i:i + 4]
        for i in range(0, len(buttons), 4)
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )
def dates_keyboard(dates: list[date]) -> InlineKeyboardMarkup:
    buttons = []

    for selected_date in dates:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=selected_date.strftime("%d.%m (%a)"),
                    callback_data=f"date:{selected_date.isoformat()}"
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
def time_keyboard(
    times: list[str]
) -> InlineKeyboardMarkup:

    buttons = [
        InlineKeyboardButton(
            text=time,
            callback_data=f"time:{time}"
        )
        for time in times
    ]

    rows = [
        buttons[i:i + 2]
        for i in range(0, len(buttons), 2)
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )
def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить консультацию — 10 €",
                    callback_data="payment:start"
                )
            ]
        ]
    )