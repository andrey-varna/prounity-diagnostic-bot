from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from services.formula import calculate_result
from bot.states import DiagnosticForm
from bot.keyboards import rating_keyboard


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Добро пожаловать в диагностику PRO Unity Consult.\n\n"
        "Вам предстоит ответить на несколько вопросов, "
        "оценив каждый показатель по предложенной шкале.\n\n"
        "Начинаем.\n\n"
        "S — оцените силу вашего внутреннего ресурса "
        "в интересующем вас направлении от 0 до 10:"
    )

    await state.set_state(DiagnosticForm.s)

    await message.answer(
        "Выберите оценку:",
        reply_markup=rating_keyboard(0, 10)
    )


@router.callback_query(
    DiagnosticForm.s,
    F.data.startswith("rating:")
)
async def process_s(
    callback: CallbackQuery,
    state: FSMContext
):
    value = int(callback.data.split(":")[1])

    if not 0 <= value <= 10:
        await callback.answer("Выберите значение от 0 до 10")
        return

    await state.update_data(s=value)

    await callback.answer()

    await callback.message.edit_text(
        f"Вы выбрали: {value}"
    )

    await state.set_state(DiagnosticForm.o)

    await callback.message.answer(
        "O — оцените уровень вашей поддержки "
        "в этом направлении от 0 до 10:",
        reply_markup=rating_keyboard(0, 10)
    )


@router.callback_query(
    DiagnosticForm.o,
    F.data.startswith("rating:")
)
async def process_o(
    callback: CallbackQuery,
    state: FSMContext
):
    value = int(callback.data.split(":")[1])

    if not 0 <= value <= 10:
        await callback.answer("Выберите значение от 0 до 10")
        return

    await state.update_data(o=value)

    await callback.answer()

    await callback.message.edit_text(
        f"Вы выбрали: {value}"
    )

    await state.set_state(DiagnosticForm.l)

    await callback.message.answer(
        "L — оцените наличие возможностей и рычагов "
        "для изменений от 0 до 10:",
        reply_markup=rating_keyboard(0, 10)
    )


@router.callback_query(
    DiagnosticForm.l,
    F.data.startswith("rating:")
)
async def process_l(
    callback: CallbackQuery,
    state: FSMContext
):
    value = int(callback.data.split(":")[1])

    if not 0 <= value <= 10:
        await callback.answer("Выберите значение от 0 до 10")
        return

    await state.update_data(l=value)

    await callback.answer()

    await callback.message.edit_text(
        f"Вы выбрали: {value}"
    )

    await state.set_state(DiagnosticForm.n)

    await callback.message.answer(
        "N — оцените степень влияния ограничивающих убеждений "
        "от 1 до 10:",
        reply_markup=rating_keyboard(1, 10)
    )

    @router.callback_query(
        DiagnosticForm.n,
        F.data.startswith("rating:")
    )
    async def process_n(
            callback: CallbackQuery,
            state: FSMContext
    ):
        value = int(callback.data.split(":")[1])

        if not 1 <= value <= 10:
            await callback.answer("Выберите значение от 1 до 10")
            return

        await state.update_data(n=value)

        await callback.answer()

        await callback.message.edit_text(
            f"Вы выбрали: {value}"
        )

        await state.set_state(DiagnosticForm.f)

        await callback.message.answer(
            "F — оцените степень влияния страхов "
            "в этом направлении от 1 до 10:",
            reply_markup=rating_keyboard(1, 10)
        )

    @router.callback_query(
        DiagnosticForm.f,
        F.data.startswith("rating:")
    )
    async def process_f(
            callback: CallbackQuery,
            state: FSMContext
    ):
        value = int(callback.data.split(":")[1])

        if not 1 <= value <= 10:
            await callback.answer("Выберите значение от 1 до 10")
            return

        await state.update_data(f=value)

        await callback.answer()

        await callback.message.edit_text(
            f"Вы выбрали: {value}"
        )

        await state.set_state(DiagnosticForm.h)

        await callback.message.answer(
            "H — оцените степень влияния привычек, "
            "которые мешают изменениям, от 1 до 10:",
            reply_markup=rating_keyboard(1, 10)
        )

    @router.callback_query(
        DiagnosticForm.h,
        F.data.startswith("rating:")
    )
    async def process_h(
            callback: CallbackQuery,
            state: FSMContext
    ):
        value = int(callback.data.split(":")[1])

        if not 1 <= value <= 10:
            await callback.answer("Выберите значение от 1 до 10")
            return

        await state.update_data(h=value)

        await callback.answer()

        await callback.message.edit_text(
            f"Вы выбрали: {value}"
        )

        # Следующим состоянием будет текстовый вопрос
        await state.set_state(DiagnosticForm.problem)

        await callback.message.answer(
            "Спасибо. Теперь коротко опишите:\n\n"
            "Что сейчас больше всего вас беспокоит "
            "в интересующем вас направлении?"
        )

        @router.message(DiagnosticForm.problem)
        async def process_problem(
                message: Message,
                state: FSMContext
        ):
            if not message.text:
                await message.answer(
                    "Пожалуйста, опишите ваш ответ текстом."
                )
                return

            await state.update_data(problem=message.text)

            await state.set_state(DiagnosticForm.desired_change)

            await message.answer(
                "Спасибо.\n\n"
                "Теперь опишите, пожалуйста:\n\n"
                "Какого изменения или результата вы хотите добиться?"
            )

        @router.message(DiagnosticForm.desired_change)
        async def process_desired_change(
                message: Message,
                state: FSMContext
        ):
            if not message.text:
                await message.answer(
                    "Пожалуйста, опишите желаемый результат текстом."
                )
                return

            await state.update_data(desired_change=message.text)

            data = await state.get_data()

            result = calculate_result(
                s=data["s"],
                o=data["o"],
                l=data["l"],
                n=data["n"],
                f=data["f"],
                h=data["h"]
            )

            await message.answer(
                "Спасибо, диагностика завершена.\n\n"
                f"Ваш общий результат R: {result['R']}\n\n"
                "Для получения персонального разбора результата "
                "и конкретных рекомендаций по вашей ситуации "
                "вы сможете записаться на консультацию."
            )

            # Пока оставляем данные в памяти.
            # Очистим состояние позже, после оплаты/записи.