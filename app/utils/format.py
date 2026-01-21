def money_space(value, decimals=2):
    try:
        return f"{float(value):,.{decimals}f}".replace(",", " ")
    except (TypeError, ValueError):
        return "0.00"
