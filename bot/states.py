from aiogram.fsm.state import State, StatesGroup


class DiagnosticForm(StatesGroup):
    s = State()
    o = State()
    l = State()

    n = State()
    f = State()
    h = State()

    problem = State()
    desired_change = State()
    consultation_date = State()
    consultation_time = State()
    payment = State()