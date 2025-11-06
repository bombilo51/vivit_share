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
@product.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        cost = request.form.get("cost")
        margin = request.form.get("marginUAH")
        new_product = Product(name=name, cost=cost)

        if margin:
            new_product.margin = margin

        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("product.products_list"))
    return render_template("product/add_product.html")

@login_required
@product.route("/delete_product/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return {"product_id": product_id, "status": "success"}, 200


@login_required
@product.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    product : Product = Product.query.get_or_404(product_id)
    marginUAH = product.margin if product.margin is not None else 0
    marginPercent = round(product.cost and (product.margin / product.cost) * 100 or 0, 2)
    marginMultiplier = round(product.cost and ((product.cost + product.margin) / product.cost) or 0, 2)
    if request.method == "POST":
        product.name = request.form.get("name")
        product.cost = request.form.get("cost")
        product.margin = request.form.get("marginUAH")
        db.session.commit()
        return redirect(url_for("product.products_list"))
    
    return render_template("product/edit_product.html", product=product, marginUAH=marginUAH, marginPercent=marginPercent, marginMultiplier=marginMultiplier)