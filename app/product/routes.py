from flask import render_template, redirect, url_for, request
from flask_login import login_required
from sqlalchemy import asc, desc, func

from . import product
from ..extensions import db
from ..models import Product


@product.route("/products_list")
@login_required
def products_list():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    q = request.args.get("q", "", type=str).strip()

    sort = request.args.get("sort", "id", type=str)
    direction = request.args.get("direction", "asc", type=str)

    query = Product.query

    if q:
        query = query.filter(func.lower(Product.name).contains(q.lower()))

    sort_map = {
        "id": Product.id,
        "name": Product.name,
        "cost": Product.cost,
        "margin": Product.margin,
        "price": Product.price,
    }
    sort_col = sort_map.get(sort, Product.id)
    sort_fn = desc if direction == "desc" else asc
    query = query.order_by(sort_fn(sort_col))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    context = dict(
        products=pagination.items,
        pagination=pagination,
        filters={
            "q": q,
            "per_page": per_page,
            "sort": sort,
            "direction": direction,
        },
    )

    # Detect AJAX request (jQuery sets this header)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        return render_template("product/_products_table.html", **context)

    return render_template("product/products_list.html", **context)


@product.route("/product/<int:product_id>")
@login_required
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product/product_detail.html", product=product)


@product.route("/add_product", methods=["GET", "POST"])
@login_required
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


@product.route("/delete_product/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return {"product_id": product_id, "status": "success"}, 200


@product.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product: Product = Product.query.get_or_404(product_id)
    marginUAH = product.margin if product.margin is not None else 0
    marginPercent = round(
        product.cost and (product.margin / product.cost) * 100 or 0, 2
    )
    marginMultiplier = round(
        product.cost and ((product.cost + product.margin) / product.cost) or 0, 2
    )
    if request.method == "POST":
        product.name = request.form.get("name")
        product.cost = request.form.get("cost")
        product.margin = request.form.get("marginUAH")
        db.session.commit()
        return redirect(url_for("product.products_list"))

    return render_template(
        "product/edit_product.html",
        product=product,
        marginUAH=marginUAH,
        marginPercent=marginPercent,
        marginMultiplier=marginMultiplier,
    )
