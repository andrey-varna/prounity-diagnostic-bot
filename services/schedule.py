from datetime import date, timedelta


WORKING_DAYS = {0, 1, 2, 3, 4}  # Понедельник–Пятница

TIME_SLOTS = [
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00",
    "19:00",
]


def get_available_dates(days_count: int = 10):
    """
    Возвращает ближайшие рабочие дни.
    """

    dates = []
    current_date = date.today()

    while len(dates) < days_count:
        if current_date.weekday() in WORKING_DAYS:
            dates.append(current_date)

        current_date += timedelta(days=1)

    return dates