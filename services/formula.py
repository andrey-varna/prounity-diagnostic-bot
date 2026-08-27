def calculate_result(
    s: int,
    o: int,
    l: int,
    n: int,
    f: int,
    h: int
) -> dict:
    """
    Расчёт авторской формулы:

    R = (S × O × L) - (N × F × H)
    """

    # S, O, L: от 0 до 10
    for value, name in [
        (s, "S"),
        (o, "O"),
        (l, "L")
    ]:
        if not 0 <= value <= 10:
            raise ValueError(
                f"{name} должен быть в диапазоне от 0 до 10"
            )

    # N, F, H: от 1 до 10
    for value, name in [
        (n, "N"),
        (f, "F"),
        (h, "H")
    ]:
        if not 1 <= value <= 10:
            raise ValueError(
                f"{name} должен быть в диапазоне от 1 до 10"
            )

    positive = s * o * l
    negative = n * f * h

    result = positive - negative

    return {
        "S": s,
        "O": o,
        "L": l,
        "N": n,
        "F": f,
        "H": h,
        "positive": positive,
        "negative": negative,
        "R": result
    }