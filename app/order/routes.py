from flask import jsonify, render_template, redirect, url_for, request
from flask_login import login_required
from . import order
from ..extensions import db
from ..models import Order, OrderItem, Product
from datetime import datetime
from collections import defaultdict
from decimal import Decimal


@order.route("/list", methods=["GET"])
@login_required
def orders_list():
    orders = Order.query.all()
    return render_template("order/list.html", orders=orders)

@order.route("/add", methods=["GET", "POST"])
@login_required
def add_order():
    products = Product.query.order_by(Product.name).all()

    if request.method == "POST":
        date_str = request.form.get("date")
        if not date_str:
            return 400, "Date is required"

        product_ids = request.form.getlist("product[]")
        quantities = request.form.getlist("quantity[]")
        unit_prices = request.form.getlist("unitPrice[]")

        created_at = datetime.fromisoformat(date_str)

        # Aggregate per product_id to avoid duplicates
        aggregated = defaultdict(lambda: {"quantity": 0, "unit_price": None})

        for pid, qty, price in zip(product_ids, quantities, unit_prices):
            if not pid or int(qty) <= 0:
                continue

            pid = int(pid)
            aggregated[pid]["quantity"] += int(qty)

            # Keep last price or enforce consistency check
            aggregated[pid]["unit_price"] = Decimal(price)

        if not aggregated:
            return 400, "Order must contain at least one product"

        # Fetch only needed products
        product_map = {
            p.id: p
            for p in Product.query.filter(Product.id.in_(aggregated.keys()))
        }

        new_order = Order(created_at=created_at)

        for pid, data in aggregated.items():
            product = product_map.get(pid)
            if not product:
                continue

            new_order.add_product(
                product=product,
                quantity=data["quantity"],
                unit_price=data["unit_price"],
            )

        db.session.add(new_order)
        db.session.commit()

        return redirect(url_for("order.orders_list"))

    return render_template("order/add.html", products=products)


@order.route("/edit/<int:order_id>", methods=["GET", "POST"])
@login_required
def edit_order(order_id):
    order: Order = Order.query.get_or_404(order_id)
    products = Product.query.order_by(Product.name).all()

    if request.method == "POST":
        date = request.form.get("date")
        product_ids = request.form.getlist("product[]")
        quantities = request.form.getlist("quantity[]")
        unit_prices = request.form.getlist("unitPrice[]")

        order.created_at = datetime.fromisoformat(date)

        for item in order.items:
            db.session.delete(item)
        db.session.commit()

        for product_id, quantity, unit_price in zip(
            product_ids, quantities, unit_prices
        ):
            if product_id and int(quantity) > 0:
                product = next((p for p in products if p.id == int(product_id)), None)
                if product:
                    order.add_product(
                        product=product, quantity=int(quantity), unit_price=unit_price
                    )

        db.session.commit()
        return redirect(url_for("order.orders_list"))

    return render_template("order/edit.html", products=products, order=order)


@login_required
@order.route("/delete_order/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    order: Order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return {"order_id": order_id, "status": "success"}, 200
