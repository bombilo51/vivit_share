from sqlalchemy import func
from decimal import Decimal
from datetime import datetime, timedelta
from ..models import Order, OrderItem, Product, SMMStats
from ..extensions import db


def get_last_day_of_month(year: int, month: int) -> datetime:
    next_month = get_next_month(year, month)
    last_day = next_month - timedelta(days=1)
    return last_day


def get_next_month(year: int, month: int) -> datetime:
    if month == 12:
        return datetime(year + 1, 1, 1)
    return datetime(year, month + 1, 1)

def get_order_data(first_day: datetime):
    first_day = first_day
    order_data = (
        db.session.query(
            func.date(Order.created_at).label("day"),
            func.count(Order.id).label("order_count"),
            func.sum(Order.total).label("total_sales"),
        )
        .filter(Order.created_at >= first_day, Order.created_at < get_next_month())
        .group_by(func.date(Order.created_at))
        .all()
    )

