from decimal import Decimal
from .models import OrderItem, Order, Product
from .extensions import db

def get_order_products(order_id: int):
    products = (
        db.session.query(Product.id, Product.name)
        .join(OrderItem, Product.id == OrderItem.product_id)
        .filter(OrderItem.order_id == order_id)
        .all()
    )
    return products
