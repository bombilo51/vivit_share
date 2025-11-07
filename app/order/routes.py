from flask import render_template, redirect, url_for, request
from flask_login import login_required
from . import order
from ..extensions import db
from ..models import Order, OrderItem, Product
from datetime import datetime


@login_required
@order.route("/list", methods=["GET"])
def orders_list():
    orders = Order.query.all()
    return render_template("order/list.html", orders=orders)


@login_required
@order.route("/add", methods=["GET", "POST"])
def add_order():
    products = Product.query.all()
    if request.method == "POST":
        date = request.form.get("date")
        product_ids = request.form.getlist("product[]")
        quantities = request.form.getlist("quantity[]")
        unit_prices = request.form.getlist("unitPrice[]")

        new_order = Order()
        new_order.created_at = datetime.fromisoformat(date)

        for product_id, quantity, unit_price in zip(product_ids, quantities, unit_prices):
            if product_id and int(quantity) > 0:
                product = next((p for p in products if p.id == int(product_id)), None)
                if product:
                    new_order.add_product(
                        product=product, quantity=int(quantity), unit_price=unit_price
                    )

        db.session.add(new_order)
        db.session.commit()

        return redirect(url_for("order.orders_list"))

    return render_template("order/add.html", products=products)
