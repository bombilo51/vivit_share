from decimal import Decimal
from sqlalchemy import Numeric
from .extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cost = db.Column(Numeric(10, 2), nullable=False)
    margin = db.Column(Numeric(5, 2), nullable=True)

    def __init__(self, name, price):
        self.name = name
        self.cost = Decimal(price)
        
    @property
    def price(self):
        if self.margin is not None:
            margin_amount = (self.cost * self.margin) / Decimal(100)
            return self.cost + margin_amount
        return self.cost
        
class OrderItem(db.Model):
    __tablename__ = "order_item"

    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    @property
    def total_price(self):
        return Decimal(self.quantity) * Decimal(self.unit_price)

    def __init__(self, product, quantity=1, unit_price=None):
        self.product = product
        self.quantity = int(quantity)
        self.unit_price = Decimal(unit_price) if unit_price is not None else Decimal(product.price)


class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def add_product(self, product, quantity=1, unit_price=None):
        for item in self.items:
            if item.product_id == product.id:
                item.quantity += int(quantity)
                return item
        item = OrderItem(product=product, quantity=quantity, unit_price=unit_price)
        self.items.append(item)
        return item

    @property
    def total(self):
        total = Decimal("0")
        for item in self.items:
            total += Decimal(item.quantity) * Decimal(item.unit_price)
        return total        
    
    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price)
                }
                for item in self.items
            ],
            "total": float(self.total)
        }