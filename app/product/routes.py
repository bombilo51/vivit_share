from flask import render_template, redirect, url_for, request
from flask_login import login_required
from . import product
from ..extensions import db
from ..models import Product


@login_required
@product.route("/products_list")
def products_list():
    products = Product.query.all()
    return render_template("product/products_list.html", products=products)


@login_required
@product.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product/product_detail.html", product=product)


@login_required
@product.route("/add_product", methods=["POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        new_product = Product(name=name, price=price)
        db.session.add(new_product)
        db.session.commit()
        return {"product": new_product, "status": "success"}, 201

@login_required
@product.route("/delete_product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return {"product_id": product_id, "status": "deleted"}, 200


@login_required
@product.route("/edit_product/<int:product_id>", methods=["POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        product.name = request.form.get("name")
        product.price = request.form.get("price")
        db.session.commit()
        return {"product": product, "status": "updated"}, 200
