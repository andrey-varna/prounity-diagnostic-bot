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
    # Используем существующее состояние problem
    # для хранения главной цели
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
    # Переходим к последнему текстовому вопросу
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
    await state.set_state(
        DiagnosticForm.consultation_time
    )
    await callback.message.answer(
        "Теперь выберите удобное время:",
        reply_markup=time_keyboard(
            TIME_SLOTS
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
    await callback.answer(
        "Создаём страницу оплаты..."
    )
    base_url = os.getenv("BASE_URL")
    if not base_url:
        await callback.message.answer(
            "Ошибка настройки системы оплаты."
        )
        return
    try:
        data = await state.get_data()
        telegram_id = callback.from_user.id
        consultation_date = data.get(
            "consultation_date"
        )
        consultation_time = data.get(
            "consultation_time"
        )
        goal = data.get("goal")
        desired_result = data.get(
            "desired_result"
        )
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
        # СОЗДАЁМ ПРЕДВАРИТЕЛЬНУЮ ЗАПИСЬ В БАЗЕ
        # ====================================================
        async with AsyncSessionLocal() as db:
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

            consultation = result.scalar_one_or_none()
            # Если записи ещё нет — создаём
            if not consultation:
                consultation = Consultation(
                    telegram_id=telegram_id,
                    goal=goal,
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
            # Если запись уже есть —
            # обновляем текстовые ответы
            else:
                consultation.goal = goal
                consultation.desired_result = (
                    desired_result
                )
                await db.commit()
        # ====================================================
        # СОЗДАЁМ STRIPE CHECKOUT SESSION
        # ====================================================
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
        # ====================================================
        # СОХРАНЯЕМ STRIPE SESSION ID
        # ====================================================
        async with AsyncSessionLocal() as db:
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
            if consultation:
                consultation.stripe_session_id = (
                    session.id
                )
                await db.commit()
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
            "Ваша консультация предварительно выбрана.\n\n"
            "Для подтверждения бронирования оплатите 10 € "
            "через защищённую страницу Stripe.",
            reply_markup=keyboard
        )
    except Exception as e:
        print(
            f"Payment error: {e}"
        )
        await callback.message.answer(
            "Не удалось создать страницу оплаты.\n\n"
            "Попробуйте позже."
        )