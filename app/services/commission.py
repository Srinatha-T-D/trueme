def get_commission_rate(level: int) -> float:
    if level == 1:
        return 0.25
    if level == 2:
        return 0.30
    if level == 3:
        return 0.40
    return 0.25
