from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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