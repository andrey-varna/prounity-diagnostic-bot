import os
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, Message,
    InlineKeyboardMarkup, InlineKeyboardButton,)
from sqlalchemy import select
from services.stripe_service import create_checkout_session
from services.formula import calculate_result
from services.schedule import get_available_dates, TIME_SLOTS
from bot.states import DiagnosticForm
from bot.keyboards import (rating_keyboard, dates_keyboard,
    time_keyboard, payment_keyboard,)
from database import AsyncSessionLocal
from models import Consultation

router = Router()
# ============================================================
# START
# ============================================================
@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext
):
    await state.clear()

    await message.answer(
        "Добро пожаловать в диагностику PRO Unity Consult.\n\n"
        "Вам предстоит пройти небольшую диагностику и ответить "
        "на несколько вопросов.\n\n"
        "Начинаем.\n\n"
        "🎯 Сначала расскажите:\n\n"
        "Какова ваша главная цель или задача сейчас?"
    )

    await state.set_state(DiagnosticForm.problem)
# ============================================================
# GOAL
# ============================================================
@router.message(DiagnosticForm.problem)
async def process_goal(
    message: Message,
    state: FSMContext
):
    if not message.text:
        await message.answer(
            "Пожалуйста, опишите вашу цель текстом."
        )
        return

    await state.update_data(
        goal=message.text
    )
    await state.set_state(DiagnosticForm.s)
    await message.answer(
        "Спасибо.\n\n"
        "Теперь оцените несколько показателей, "
        "связанных с вашей целью.\n\n"
        "S — оцените силу вашего внутреннего ресурса "
        "в интересующем вас направлении от 0 до 10:",
        reply_markup=rating_keyboard(0, 10)
    )
# ============================================================
# S
# ============================================================
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
        await callback.answer(
            "Выберите значение от 0 до 10"
        )
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
# ============================================================
# O
# ============================================================
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
        await callback.answer(
            "Выберите значение от 0 до 10"
        )
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
# ============================================================
# L
# ============================================================
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
        await callback.answer(
            "Выберите значение от 0 до 10"
        )
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
# ============================================================
# N
# ============================================================
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
        await callback.answer(
            "Выберите значение от 1 до 10"
        )
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
# ============================================================
# F
# ============================================================
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
        await callback.answer(
            "Выберите значение от 1 до 10"
        )
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
# ============================================================
# H
# ============================================================
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
        await callback.answer(
            "Выберите значение от 1 до 10"
        )
        return
    await state.update_data(h=value)
    await callback.answer()
    await callback.message.edit_text(
        f"Вы выбрали: {value}"
    )
    await state.set_state(DiagnosticForm.desired_change)
    await callback.message.answer(
        "Спасибо.\n\n"
        "✨ Теперь последний вопрос:\n\n"
        "Какого результата вы хотите добиться?"
    )
# ============================================================
# DESIRED RESULT
# ============================================================
@router.message(DiagnosticForm.desired_change)
async def process_desired_result(
    message: Message,
    state: FSMContext
):
    if not message.text:
        await message.answer(
            "Пожалуйста, опишите желаемый результат текстом."
        )
        return
    await state.update_data(
        desired_result=message.text
    )
    data = await state.get_data()
    result = calculate_result(
        s=data["s"],
        o=data["o"],
        l=data["l"],
        n=data["n"],
        f=data["f"],
        h=data["h"]
    )
    await state.update_data(
        diagnostic_result=result
    )
    available_dates = get_available_dates()
    await state.set_state(
        DiagnosticForm.consultation_date
    )
    await message.answer(
        "Спасибо. Диагностика завершена.\n\n"
        "Ваши ответы обработаны по авторской методике "
        "PRO Unity Consult.\n\n"
        "На персональной консультации вы получите:\n"
        "• разбор вашего результата;\n"
        "• анализ вашей конкретной ситуации;\n"
        "• рекомендации по улучшению интересующего "
        "вас направления.\n\n"
        "Продолжительность первой консультации — 60 минут.\n"
        "Стоимость бронирования — 10 €.\n\n"
        "Выберите удобную дату:"
    )
    await message.answer(
        "Ближайшие доступные рабочие дни:",
        reply_markup=dates_keyboard(
            available_dates
        )
    )
# ============================================================
# CONSULTATION DATE
# ============================================================
@router.callback_query(
    DiagnosticForm.consultation_date,
    F.data.startswith("date:")
)
async def process_consultation_date(
    callback: CallbackQuery,
    state: FSMContext
):
    selected_date = callback.data.split(
        ":",
        1
    )[1]
    await state.update_data(
        consultation_date=selected_date
    )
    await callback.answer()
    await callback.message.edit_text(
        f"Вы выбрали дату: {selected_date}"
    )
    # Получаем занятые слоты на выбранную дату
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                Consultation.consultation_time
            ).where(
                Consultation.consultation_date
                == selected_date,
                Consultation.payment_status.in_(
                    ["pending", "paid"]
                )
            )
        )
        occupied_times = set(
            result.scalars().all()
        )
    # Формируем список свободных слотов
    free_times = [
        time
        for time in TIME_SLOTS
        if time not in occupied_times
    ]
    # Если на дату мест больше нет
    if not free_times:
        await callback.message.answer(
            "😔 На выбранную дату свободных мест "
            "уже нет.\n\n"
            "Пожалуйста, выберите другую дату."
        )
        available_dates = get_available_dates()
        await callback.message.answer(
            "Ближайшие доступные рабочие дни:",
            reply_markup=dates_keyboard(
                available_dates
            )
        )
        return
    # Показываем только свободное время
    await state.set_state(
        DiagnosticForm.consultation_time
    )
    await callback.message.answer(
        "Теперь выберите удобное свободное время:",
        reply_markup=time_keyboard(
            free_times
        )
    )
# ============================================================
# CONSULTATION TIME
# ============================================================
@router.callback_query(
    DiagnosticForm.consultation_time,
    F.data.startswith("time:")
)
async def process_consultation_time(
    callback: CallbackQuery,
    state: FSMContext
):
    selected_time = callback.data.split(
        ":",
        1
    )[1]
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
    await state.set_state(
        DiagnosticForm.payment
    )
    await callback.message.answer(
        "Нажмите кнопку ниже для перехода к оплате:",
        reply_markup=payment_keyboard()
    )
# ============================================================
# PAYMENT START
# ============================================================
@router.callback_query(
    DiagnosticForm.payment,
    F.data == "payment:start"
)
async def process_payment_start(
    callback: CallbackQuery,
    state: FSMContext
):
    print("=" * 50)
    print("PAYMENT BUTTON CLICKED")
    print(f"User: {callback.from_user.id}")
    print(f"Callback data: {callback.data}")
    print("=" * 50)

    await callback.answer(
        "Проверяем доступность времени..."
    )

    base_url = os.getenv("BASE_URL")

    if not base_url:
        await callback.message.answer(
            "Ошибка настройки системы оплаты."
        )
        return

    try:
        # ====================================================
        # ПОЛУЧАЕМ ДАННЫЕ ИЗ FSM
        # ====================================================
        data = await state.get_data()

        telegram_id = callback.from_user.id

        consultation_date = data.get(
            "consultation_date"
        )

        consultation_time = data.get(
            "consultation_time"
        )

        goal = data.get("goal")

        s = data.get("s")
        o = data.get("o")
        l = data.get("l")
        n = data.get("n")
        f = data.get("f")
        h = data.get("h")

        result_data = data.get(
            "diagnostic_result"
        )

        # calculate_result возвращает словарь,
        # в базе сохраняем только итоговое значение R
        if isinstance(result_data, dict):
            diagnostic_result = result_data.get("R")
        else:
            diagnostic_result = result_data

        desired_result = data.get(
            "desired_result"
        )

        print("=" * 50)
        print("PAYMENT DATA")
        print(f"Telegram ID: {telegram_id}")
        print(f"Date: {consultation_date}")
        print(f"Time: {consultation_time}")
        print(f"Goal: {goal}")
        print(f"S={s}, O={o}, L={l}")
        print(f"N={n}, F={f}, H={h}")
        print(
            f"Diagnostic result: "
            f"{diagnostic_result}"
        )
        print(
            f"Desired result: "
            f"{desired_result}"
        )
        print("=" * 50)

        # ====================================================
        # ПРОВЕРЯЕМ ДАТУ И ВРЕМЯ
        # ====================================================
        if (
            not consultation_date
            or not consultation_time
        ):
            await callback.message.answer(
                "Не удалось определить дату или время "
                "консультации.\n\n"
                "Пожалуйста, начните бронирование заново."
            )
            return

        # ====================================================
        # СОЗДАЁМ ИЛИ ОБНОВЛЯЕМ ЗАПИСЬ
        # ====================================================
        async with AsyncSessionLocal() as db:

            # ------------------------------------------------
            # ПРОВЕРЯЕМ, НЕ ЗАНЯТ ЛИ СЛОТ ДРУГИМ КЛИЕНТОМ
            # ------------------------------------------------
            result = await db.execute(
                select(Consultation).where(
                    Consultation.consultation_date
                    == consultation_date,

                    Consultation.consultation_time
                    == consultation_time,

                    Consultation.payment_status.in_(
                        ["pending", "paid"]
                    ),

                    Consultation.telegram_id
                    != telegram_id
                )
            )

            occupied_consultation = (
                result.scalar_one_or_none()
            )

            if occupied_consultation:

                print(
                    "SLOT OCCUPIED BY CONSULTATION ID: "
                    f"{occupied_consultation.id}"
                )

                await callback.message.answer(
                    "😔 К сожалению, это время только что "
                    "было выбрано другим клиентом.\n\n"
                    "Пожалуйста, начните выбор времени заново."
                )

                return

            # ------------------------------------------------
            # ИЩЕМ СУЩЕСТВУЮЩУЮ PENDING-ЗАПИСЬ
            # ЭТОГО ЖЕ КЛИЕНТА
            # ------------------------------------------------
            result = await db.execute(
                select(Consultation).where(
                    Consultation.telegram_id
                    == telegram_id,

                    Consultation.consultation_date
                    == consultation_date,

                    Consultation.consultation_time
                    == consultation_time,

                    Consultation.payment_status
                    == "pending"
                )
            )

            consultation = (
                result.scalar_one_or_none()
            )

            # ------------------------------------------------
            # СОЗДАЁМ НОВУЮ ЗАПИСЬ
            # ------------------------------------------------
            if not consultation:

                print(
                    "CREATING NEW CONSULTATION..."
                )

                consultation = Consultation(
                    telegram_id=telegram_id,
                    goal=goal,

                    s=s,
                    o=o,
                    l=l,

                    n=n,
                    f=f,
                    h=h,

                    diagnostic_result=diagnostic_result,

                    desired_result=desired_result,

                    consultation_date=consultation_date,
                    consultation_time=consultation_time,

                    payment_status="pending",
                    is_processed=False
                )

                db.add(consultation)

                await db.commit()

                await db.refresh(
                    consultation
                )

                print("=" * 50)
                print(
                    "CONSULTATION CREATED SUCCESSFULLY"
                )
                print(
                    f"Consultation ID: "
                    f"{consultation.id}"
                )
                print("=" * 50)

            # ------------------------------------------------
            # ОБНОВЛЯЕМ СУЩЕСТВУЮЩУЮ ЗАПИСЬ
            # ------------------------------------------------
            else:

                print("=" * 50)
                print(
                    "UPDATING EXISTING CONSULTATION"
                )
                print(
                    f"Consultation ID: "
                    f"{consultation.id}"
                )
                print("=" * 50)

                consultation.goal = goal

                consultation.s = s
                consultation.o = o
                consultation.l = l

                consultation.n = n
                consultation.f = f
                consultation.h = h

                consultation.diagnostic_result = (
                    diagnostic_result
                )

                consultation.desired_result = (
                    desired_result
                )

                await db.commit()

                await db.refresh(
                    consultation
                )

                print(
                    "CONSULTATION UPDATED SUCCESSFULLY"
                )

            # Сохраняем ID записи
            consultation_id = consultation.id

        # ====================================================
        # СОЗДАЁМ STRIPE CHECKOUT SESSION
        # ====================================================
        print("=" * 50)
        print("CREATING STRIPE SESSION")
        print(
            f"Consultation ID: {consultation_id}"
        )
        print("=" * 50)

        session = await create_checkout_session(
            success_url=(
                f"{base_url}/payment/success"
            ),
            cancel_url=(
                f"{base_url}/payment/cancel"
            ),
            telegram_id=telegram_id,
            consultation_date=consultation_date,
            consultation_time=consultation_time,
        )

        print(
            f"STRIPE SESSION CREATED: "
            f"{session.id}"
        )

        # ====================================================
        # СОХРАНЯЕМ STRIPE SESSION ID
        # ====================================================
        async with AsyncSessionLocal() as db:

            result = await db.execute(
                select(Consultation).where(
                    Consultation.id
                    == consultation_id
                )
            )

            consultation = (
                result.scalar_one_or_none()
            )

            if consultation:

                consultation.stripe_session_id = (
                    session.id
                )

                await db.commit()

                print("=" * 50)
                print(
                    "STRIPE SESSION ID SAVED"
                )
                print(
                    f"Consultation ID: "
                    f"{consultation.id}"
                )
                print(
                    f"Stripe Session: "
                    f"{session.id}"
                )
                print("=" * 50)

            else:

                print(
                    "ERROR: CONSULTATION NOT FOUND "
                    "WHEN SAVING STRIPE SESSION"
                )

        # ====================================================
        # КНОПКА ОПЛАТЫ
        # ====================================================
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=(
                            "💳 Перейти к оплате 10 €"
                        ),
                        url=session.url
                    )
                ]
            ]
        )

        await callback.message.answer(
            "Ваша консультация предварительно "
            "зарезервирована.\n\n"
            "Для окончательного подтверждения "
            "оплатите 10 € через защищённую "
            "страницу Stripe.",
            reply_markup=keyboard
        )

    except Exception as e:

        print("=" * 50)
        print("PAYMENT ERROR")
        print(type(e).__name__)
        print(str(e))
        print("=" * 50)

        await callback.message.answer(
            "Не удалось создать страницу оплаты.\n\n"
            "Попробуйте позже."
        )