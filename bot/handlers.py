from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from services.formula import calculate_result
from bot.states import DiagnosticForm
from bot.keyboards import (
    rating_keyboard,
    dates_keyboard,
    time_keyboard,
    payment_keyboard
)
from services.schedule import get_available_dates, TIME_SLOTS

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
                "Спасибо. Диагностика завершена.\n\n"
                "Ваши ответы обработаны по авторской методике PRO Unity Consult.\n\n"
                "На персональной консультации вы получите:\n"
                "• разбор вашего результата;\n"
                "• анализ вашей конкретной ситуации;\n"
                "• рекомендации по улучшению интересующего вас направления.\n\n"
                "Продолжительность первой консультации — 60 минут.\n"
                "Стоимость бронирования — 10 €.\n\n"
                "Выберите удобную дату:"
            )
            available_dates = get_available_dates()

            await state.set_state(DiagnosticForm.consultation_date)

            await message.answer(
                "Ближайшие доступные рабочие дни:",
                reply_markup=dates_keyboard(available_dates)
            )

            @router.callback_query(
                DiagnosticForm.consultation_date,
                F.data.startswith("date:")
            )
            async def process_consultation_date(
                    callback: CallbackQuery,
                    state: FSMContext
            ):
                selected_date = callback.data.split(":", 1)[1]

                await state.update_data(
                    consultation_date=selected_date
                )

                await callback.answer()

                await callback.message.edit_text(
                    f"Вы выбрали дату: {selected_date}"
                )

                await state.set_state(
                    DiagnosticForm.consultation_time
                )

                await callback.message.answer(
                    "Теперь выберите удобное время:",
                    reply_markup=time_keyboard(TIME_SLOTS)
                )

            @router.callback_query(
                DiagnosticForm.consultation_time,
                F.data.startswith("time:")
            )
            async def process_consultation_time(
                    callback: CallbackQuery,
                    state: FSMContext
            ):
                selected_time = callback.data.split(":", 1)[1]

                await state.update_data(
                    consultation_time=selected_time
                )

                await callback.answer()

                data = await state.get_data()

                selected_date = data.get(
                    "consultation_date"
                )

                await callback.message.edit_text(
                    f"Вы выбрали время: {selected_time}"
                )

                await callback.message.answer(
                    "Ваше предварительное время консультации:\n\n"
                    f"📅 Дата: {selected_date}\n"
                    f"🕒 Время: {selected_time}–"
                    f"{int(selected_time[:2]) + 1:02d}:00\n\n"
                    "Для окончательного бронирования необходимо "
                    "оплатить 10 €.\n\n"
                    "После успешной оплаты выбранное время будет "
                    "закреплено за вами."
                )
                await state.set_state(DiagnosticForm.payment)

                await callback.message.answer(
                    "Нажмите кнопку ниже для перехода к оплате:",
                    reply_markup=payment_keyboard()
                )

                @router.callback_query(
                    DiagnosticForm.payment,
                    F.data == "payment:start"
                )
                async def process_payment_start(
                        callback: CallbackQuery,
                        state: FSMContext
                ):
                    await callback.answer()

                    await callback.message.answer(
                        "Система оплаты будет подключена на следующем этапе.\n\n"
                        "Сейчас мы проверяем полную логику воронки."
                    )
            # Пока оставляем данные в памяти.
            # Очистим состояние позже, после оплаты/записи.