import os
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    FSInputFile,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from services.stripe_service import create_checkout_session
from services.formula import (calculate_result, interpret_result,
    explain_positive_balance,)
from services.schedule import get_available_dates, TIME_SLOTS
from bot.states import DiagnosticForm
from bot.keyboards import (rating_keyboard, dates_keyboard,
    time_keyboard, payment_keyboard,)
from database import AsyncSessionLocal
from models import Consultation

router = Router()

# ============================================================
# НАСТРОЙКИ
# ============================================================
# Сколько минут "живёт" незавершённая (pending) запись,
# после чего слот считается снова свободным для других
PENDING_TTL_MINUTES = 30
# Username бота без "@", нужен для deep link после оплаты
# (например "unity_consult_bot"). Задать в .env
BOT_USERNAME = os.getenv("BOT_USERNAME")


def _pending_cutoff() -> datetime:
    """Момент времени, старее которого pending-записи не блокируют слот."""
    return datetime.utcnow() - timedelta(minutes=PENDING_TTL_MINUTES)
# ============================================================
# START
# Обычный запуск / deep link / возврат после оплаты
# ============================================================
@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
    command: CommandObject,
):
    payload = command.args or ""
    print(
        f"START RECEIVED | telegram_id={message.from_user.id} "
        f"| message={message.text!r} "
        f"| command_args={command.args!r}"
    )

    # --------------------------------------------------------
    # Возврат из Stripe после оплаты:
    # /start paid_<consultation_id>
    # --------------------------------------------------------
    if payload.startswith("paid_"):
        raw_id = payload.removeprefix("paid_")

        if raw_id.isdigit():
            consultation_id = int(raw_id)

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Consultation).where(
                        Consultation.id == consultation_id
                    )
                )
                consultation = result.scalar_one_or_none()

            if consultation and consultation.payment_status == "paid":
                await message.answer(
                    "✅ Оплата подтверждена!\n\n"
                    f"📅 Дата: {consultation.consultation_date}\n"
                    f"🕒 Время: {consultation.consultation_time}\n\n"
                    "Наставники свяжутся с вами перед встречей. "
                    "До скорого!"
                )
            else:
                await message.answer(
                    "⏳ Оплата обрабатывается.\n\n"
                    "Обычно это занимает несколько секунд. "
                    "Если статус не обновится в течение пары минут — "
                    "напишите нам, мы всё проверим вручную."
                )

            return

    # --------------------------------------------------------
    # Обычный запуск или рекламный deep link
    # --------------------------------------------------------
    await state.clear()

    ad_source = payload or "organic"

    await state.update_data(
        ad_source=ad_source
    )

    print(
        f"START | telegram_id={message.from_user.id} "
        f"| payload={payload!r} "
        f"| ad_source={ad_source!r}"
    )

    await _send_welcome(message, state)

async def _send_welcome(message: Message, state: FSMContext):
    photo = FSInputFile(
        "images/welcome_photo.jpg"
    )

    await message.answer_photo(
        photo=photo,
        caption=(
            "Добро пожаловать в диагностику PRO Unity Consult.\n\n"
            "За 2 минуты вы сможете оценить состояние вашей системы "
            "по Формуле PROрезультат и увидите, "
            "где у вас скрыт мощный ресурс, а что забирает силы.\n\n"
            "Начинаем.\n\n"
            "Шаг 1 из 3. Ваша текущая ситуация\n\n"
            "🎯 Опишите в 1–2 предложениях: с каким главным вызовом или задачей "
            "в бизнесе/жизни вы сталкиваетесь прямо сейчас?:\n\n"
            "(Например: выгорание, потолок в доходе, микроконтроль, напряжение в семье)"
        )
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
            "Пожалуйста, введите ответ текстом."
        )
        return

    await state.update_data(
        goal=message.text
    )
    await state.set_state(DiagnosticForm.s)
    await message.answer(
        "Отлично, приняли.\n\n"
        "Шаг 2. Оценка по Формуле (Баллы 0–10).\n\n"
        "Теперь давайте разложим вашу задачу по Формуле PROрезультат. \n\n"
        "Оцените 6 показателей от 0 до 10, опираясь на свои ощущения:\n\n"
        "•  S (Сила)-Ваш внутренний ресурс: Насколько вы полны энергии, "
        "вдохновения и физических сил для решения этой задачи?\n\n"
        "[ 0-Полное истощение/воля ] ↔ [10-Огромный драйв и энергия]",
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
        "•  O (Опоры) — Качество вашей поддержки: \n\n "
        "Насколько вы чувствуете надежный тыл\n"
        "(понимание в семье, личные ценности, верное окружение)?\n\n"
        "[0-Одиночество] ↔ [10-Мощная поддержка и тепло]",
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
        "•  L (Рычаги) — Управление и система:\n\n"
        "Насколько у вас есть понятные инструменты,\n"
        "навыки и стратегия (без необходимости тушить пожары 24/7)?\n\n "
        "[0-Хаос и микроменеджмент] ↔ [10-Четкая работающая система]\n",
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
        "А теперь оцените «барьеры»\n"
        " - то, что незаметно тормозит движение:\n\n"
        "•N (Негативные убеждения):\n"
        "Степень влияния установок вроде «надо пахать до износа» \n"
        "или «масштаб — это боль».\n\n"
        "[1-Не мешают] ↔ [10-Постоянно упираюсь в потолок]:",
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
        "•  F (Страхи): Уровень фоновой тревоги\n "
        "(страх прогореть, потерять контроль, не оправдать ожиданий).\n\n"
        "[1-Спокойствие и уверенность] ↔ [10-Сильный фоновый страх]",
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
        "•  H (Привычки):\n"
        " Насколько часто вы наступаете на одни и те же грабли в кризисных ситуациях?\n\n "
        "[1-Действую осознанно] ↔ [10-Регулярно срываюсь в старые сценарии]",
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
        "Принято! Остался финальный штрих\n\n"
        "Шаг 3 из 3. Желаемый результат\n\n"
        "Представьте, что прошла наша совместная работа и вы пересобрали свою систему.\n\n"
        "Как выглядит ваш идеальный результат через 3–6 месяцев?\n "
        "Что изменилось в бизнесе, вашем состоянии и отношениях?\n"
        "(Опишите желаемую картину текстом)\n\n"
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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔎 Получить краткую расшифровку",
                    callback_data="result:interpretation"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Записаться на консультацию",
                    callback_data="payment:start"
                )
            ]
        ]
    )

    await message.answer(
        "Благодарим за честность! Ваш профиль сформирован.\n\n"
        "Ваши ответы обработаны по авторской методике и "
        "отправлены наставникам — Татьяне и Андрею Прокопчук.\n\n"

        "📊 Ваш результат диагностики:\n"
        f"R = {result['R']}\n"
        "Это ваш текущий показатель по Формуле PROрезультат. "
        "Его краткую расшифровку вы можете увидеть, нажав кнопку ниже.\n"
        "А на личной встрече мы можем разобрать, за счёт каких факторов "
        "он сформирован и где находятся ваши точки роста.\n\n"

        "Стоимость фиксации слота: 10 €.\n"
        "(Это фильтр серьёзности: гарантирует, что время наставников "
        "не займёт тот, кто потом не придёт).\n\n"

        "Выберите действие:",
        reply_markup=keyboard
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

    # Занятыми считаем: все "paid" + "pending", созданные недавно
    # (старые pending истекли и не блокируют слот)
    cutoff = _pending_cutoff()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                Consultation.consultation_time
            ).where(
                Consultation.consultation_date == selected_date,
                (
                    (Consultation.payment_status == "paid")
                    | (
                        (Consultation.payment_status == "pending")
                        & (Consultation.created_at >= cutoff)
                    )
                ),
            )
        )
        occupied_times = set(
            result.scalars().all()
        )

    free_times = [
        time
        for time in TIME_SLOTS
        if time not in occupied_times
    ]

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
        "подтвердить выбранное время и оплатить 10 €.\n\n"
        "После успешной оплаты выбранное время будет "
        "закреплено за вами."
    )
    await state.set_state(
        DiagnosticForm.payment
    )
    confirmation_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить выбранное время",
                    callback_data="payment:start"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Выбрать другие дату/время",
                    callback_data="booking:change"
                )
            ]
        ]
    )

    await callback.message.answer(
        "Подтвердить выбранное время:",
        reply_markup=confirmation_keyboard
    )


# ============================================================
# CHANGE CONSULTATION DATE/TIME
# ============================================================
@router.callback_query(
    DiagnosticForm.payment,
    F.data == "booking:change"
)
async def change_consultation_datetime(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()

    await state.update_data(
        consultation_date=None,
        consultation_time=None
    )

    await state.set_state(
        DiagnosticForm.consultation_date
    )

    available_dates = get_available_dates()

    await callback.message.answer(
        "Ближайшие доступные рабочие дни:",
        reply_markup=dates_keyboard(
            available_dates
        )
    )


# ============================================================
# RESULT INTERPRETATION
# ============================================================
@router.callback_query(
    F.data == "result:interpretation"
)
async def show_result_interpretation(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    result_data = data.get("diagnostic_result")

    if isinstance(result_data, dict):
        diagnostic_result = result_data.get("R")
    else:
        diagnostic_result = result_data

    if diagnostic_result is None:
        await callback.answer(
            "Результат диагностики не найден.",
            show_alert=True
        )
        return

    result_interpretation = interpret_result(
        diagnostic_result
    )

    balance_explanation = explain_positive_balance(
        s=data["s"],
        o=data["o"],
        l=data["l"]
    )

    additional_text = ""

    if balance_explanation:
        additional_text = (
            "\n\n"
            + balance_explanation
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Записаться на консультацию",
                    callback_data="payment:start"
                )
            ]
        ]
    )

    await callback.answer()

    await callback.message.answer(
        "🔎 Краткая расшифровка вашего результата\n\n"
        f"📊 Ваш результат: R = {diagnostic_result}\n\n"
        f"{result_interpretation}"
        f"{additional_text}\n\n"
        "💡 Это первичная картина по Формуле PROрезультат. "
        "На личной 60-минутной встрече мы сможем разобрать "
        "ваш результат глубже: увидеть, какие именно факторы "
        "формируют его сейчас и где находится наиболее сильная "
        "точка роста именно для вашей ситуации.",
        reply_markup=keyboard
    )


# ============================================================
# PAYMENT START
# ============================================================
@router.callback_query(
    F.data == "payment:start"
)
async def process_payment_start(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer(
        "Проверяем доступность времени..."
    )

    data = await state.get_data()

    if not data.get("consultation_date"):
        available_dates = get_available_dates()

        await state.set_state(
            DiagnosticForm.consultation_date
        )

        await callback.message.answer(
            "Ближайшие доступные рабочие дни:",
            reply_markup=dates_keyboard(
                available_dates
            )
        )
        return

    base_url = os.getenv("BASE_URL")

    if not base_url:
        await callback.message.answer(
            "Ошибка настройки системы оплаты."
        )
        return

    if not BOT_USERNAME:
        await callback.message.answer(
            "Ошибка настройки системы оплаты."
        )
        return

    try:
        data = await state.get_data()

        telegram_id = callback.from_user.id

        consultation_date = data.get("consultation_date")
        consultation_time = data.get("consultation_time")
        goal = data.get("goal")

        s = data.get("s")
        o = data.get("o")
        l = data.get("l")
        n = data.get("n")
        f = data.get("f")
        h = data.get("h")

        result_data = data.get("diagnostic_result")

        if isinstance(result_data, dict):
            diagnostic_result = result_data.get("R")
        else:
            diagnostic_result = result_data

        desired_result = data.get("desired_result")

        # атрибуция рекламы — сохранена ещё на /start
        ad_source = data.get("ad_source", "organic")

        if not consultation_date or not consultation_time:
            await callback.message.answer(
                "Не удалось определить дату или время "
                "консультации.\n\n"
                "Пожалуйста, начните бронирование заново."
            )
            return

        cutoff = _pending_cutoff()

        async with AsyncSessionLocal() as db:

            # ------------------------------------------------
            # ПРОВЕРЯЕМ, НЕ ЗАНЯТ ЛИ СЛОТ ДРУГИМ КЛИЕНТОМ
            # (paid — всегда занято; pending — только если "свежий")
            # ------------------------------------------------
            result = await db.execute(
                select(Consultation).where(
                    Consultation.consultation_date == consultation_date,
                    Consultation.consultation_time == consultation_time,
                    Consultation.telegram_id != telegram_id,
                    (
                        (Consultation.payment_status == "paid")
                        | (
                            (Consultation.payment_status == "pending")
                            & (Consultation.created_at >= cutoff)
                        )
                    ),
                )
            )

            occupied_consultation = result.scalar_one_or_none()

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
            # ИЩЕМ СУЩЕСТВУЮЩУЮ PENDING-ЗАПИСЬ ЭТОГО ЖЕ КЛИЕНТА
            # ------------------------------------------------
            result = await db.execute(
                select(Consultation).where(
                    Consultation.telegram_id == telegram_id,
                    Consultation.consultation_date == consultation_date,
                    Consultation.consultation_time == consultation_time,
                    Consultation.payment_status == "pending",
                )
            )

            consultation = result.scalar_one_or_none()

            try:
                if not consultation:
                    print("CREATING NEW CONSULTATION...")

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
                        is_processed=False,
                        ad_source=ad_source,
                    )

                    db.add(consultation)
                    await db.commit()
                    await db.refresh(consultation)

                    print("=" * 50)
                    print("CONSULTATION CREATED SUCCESSFULLY")
                    print(f"Consultation ID: {consultation.id}")
                    print("=" * 50)

                else:
                    consultation.goal = goal
                    consultation.s = s
                    consultation.o = o
                    consultation.l = l
                    consultation.n = n
                    consultation.f = f
                    consultation.h = h
                    consultation.diagnostic_result = diagnostic_result
                    consultation.desired_result = desired_result
                    consultation.ad_source = ad_source

                    await db.commit()
                    await db.refresh(consultation)

            except IntegrityError:
                # Сработал уникальный индекс на (date, time, active-статус) —
                # значит слот заняли буквально в последнюю миллисекунду
                await db.rollback()
                print("SLOT TAKEN AT DB LEVEL (IntegrityError)")
                await callback.message.answer(
                    "😔 К сожалению, это время только что "
                    "было выбрано другим клиентом.\n\n"
                    "Пожалуйста, начните выбор времени заново."
                )
                return

            consultation_id = consultation.id

        # ====================================================
        # СОЗДАЁМ STRIPE CHECKOUT SESSION
        # ====================================================
        print("=" * 50)
        print("CREATING STRIPE SESSION")
        print(f"Consultation ID: {consultation_id}")
        print("=" * 50)

        # success_url ведёт обратно в Telegram через deep link,
        # чтобы после оплаты пользователь не "застревал" в браузере
        success_url = (
            f"https://t.me/{BOT_USERNAME}?start=paid_{consultation_id}"
        )
        cancel_url = f"{base_url}/payment/cancel"

        session = await create_checkout_session(
            success_url=success_url,
            cancel_url=cancel_url,
            telegram_id=telegram_id,
            consultation_date=consultation_date,
            consultation_time=consultation_time,
            metadata={
                "consultation_id": str(consultation_id),
                "ad_source": ad_source,
            },
        )

        print(f"STRIPE SESSION CREATED: {session.id}")

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Consultation).where(
                    Consultation.id == consultation_id
                )
            )
            consultation = result.scalar_one_or_none()

            if consultation:
                consultation.stripe_session_id = session.id
                await db.commit()

                print("=" * 50)
                print("STRIPE SESSION ID SAVED")
                print(f"Consultation ID: {consultation.id}")
                print(f"Stripe Session: {session.id}")
                print("=" * 50)
            else:
                print(
                    "ERROR: CONSULTATION NOT FOUND "
                    "WHEN SAVING STRIPE SESSION"
                )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Оплатить резервирование 10 евро",
                        url=session.url
                    )
                ]
            ]
        )

        await callback.message.answer(
            "Ваша консультация предварительно "
            "зарезервирована.\n\n"
            "Для окончательного подтверждения "
            "оплатите 10 €",
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