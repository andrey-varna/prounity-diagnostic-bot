from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True
    )

    # Главная цель клиента перед началом опроса
    goal: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Оценки по формуле
    s: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    o: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    l: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    n: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    f: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    h: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    # Рассчитанный результат диагностики
    diagnostic_result: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    # Желаемый результат клиента
    desired_result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Дата и время консультации.
    # До бронирования могут быть NULL.
    consultation_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    consultation_time: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True
    )

    stripe_session_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True
    )

    payment_status: Mapped[str] = mapped_column(
        String(30),
        default="not_started",
        nullable=False
    )

    is_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    ad_source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default="organic"
    )

    # Текущий этап воронки
    funnel_stage: Mapped[str] = mapped_column(
        String(30),
        default="started",
        nullable=False
    )