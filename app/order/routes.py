from collections import defaultdict
from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required
from sqlalchemy import desc, asc, func, distinct
from sqlalchemy.orm import selectinload

from . import order
from .. import normalize_text
from ..extensions import db
from ..models import Order, OrderItem, Product


@order.route("/unit_names", methods=["GET"])
@login_required
def order_unit_names():
    term = request.args.get("term", "", type=str).strip()
    term_norm = normalize_text(term)

    start = request.args.get("start", "", type=str).strip()  # YYYY-MM-DD
    end = request.args.get("end", "", type=str).strip()  # YYYY-MM-DD
    order_id = request.args.get("order_id", "", type=str).strip()

    # Current selected items (multi)
    selected = request.args.getlist("selected[]") or request.args.getlist("selected")
    selected_norm = sorted({normalize_text(x) for x in selected if normalize_text(x)})

    # Base: unit_name values that appear in order_item
    base = (
        db.session.query(OrderItem.unit_name, OrderItem.unit_name_search)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(OrderItem.unit_name_search.isnot(None))
    )

    if selected_norm:
        base = base.filter(~OrderItem.unit_name_search.in_(selected_norm))

    # Apply optional order-level filters to options too (so options match current list filters)
    if order_id and order_id.isdigit():
        base = base.filter(Order.id == int(order_id))

    if start:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        base = base.filter(Order.created_at >= start_dt)

    if end:
        end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
        base = base.filter(Order.created_at < end_dt)

    # If user already selected some items, only offer options that can co-exist with them
    # i.e., options that appear in orders that contain ALL selected items.
    if selected_norm:
        orders_with_all_selected = (
            db.session.query(OrderItem.order_id)
            .filter(OrderItem.unit_name_search.in_(selected_norm))
            .group_by(OrderItem.order_id)
            .having(func.count(distinct(OrderItem.unit_name_search)) == len(selected_norm))
            .subquery()
        )
        base = base.filter(OrderItem.order_id.in_(orders_with_all_selected))

    # Text search on options (case-insensitive via normalized column)
    if term_norm:
        base = base.filter(OrderItem.unit_name_search.contains(term_norm))

    # Distinct options
    rows = (
        base.group_by(OrderItem.unit_name, OrderItem.unit_name_search)
        .order_by(OrderItem.unit_name)
        .limit(50)
        .all()
    )

    results = [{"id": name, "text": name} for name, _ in rows if name]
    return jsonify({"results": results})


@order.route("/list", methods=["GET"])
@login_required
def orders_list():
    items = OrderItem.query.all()
    for item in items:
        item.unit_name_search = normalize_text(item.unit_name)

    db.session.commit()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    order_id = request.args.get("order_id", "", type=str).strip()
    start = request.args.get("start", "", type=str).strip()
    end = request.args.get("end", "", type=str).strip()

    unit_names = request.args.getlist("unit_names")  # multi-select values (display strings)
    sort = request.args.get("sort", "created_at", type=str)
    direction = request.args.get("direction", "desc", type=str)

    query = Order.query.options(selectinload(Order.items))

    if order_id and order_id.isdigit():
        query = query.filter(Order.id == int(order_id))

    if start:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        query = query.filter(Order.created_at >= start_dt)

    if end:
        end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Order.created_at < end_dt)

    # AND semantics: order must contain ALL selected unit_names
    if unit_names:
        normalized = sorted({normalize_text(n) for n in unit_names if normalize_text(n)})
        if normalized:
            query = (
                query
                .join(OrderItem)
                .filter(OrderItem.unit_name_search.in_(normalized))
                .group_by(Order.id)
                .having(func.count(distinct(OrderItem.unit_name_search)) == len(normalized))
            )

    sort_map = {"id": Order.id, "created_at": Order.created_at}
    sort_col = sort_map.get(sort, Order.created_at)
    sort_fn = desc if direction == "desc" else asc
    query = query.order_by(sort_fn(sort_col))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    context = dict(
        orders=pagination.items,
        pagination=pagination,
        filters={
            "order_id": order_id,
            "start": start,
            "end": end,
            "unit_names": unit_names,  # keep selected in form
            "per_page": per_page,
            "sort": sort,
            "direction": direction,
        },
    )

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        return render_template("order/_orders_table.html", **context)

    return render_template("order/list.html", **context)


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
        unit_margins = request.form.getlist("unitMargin[]")
        created_at = datetime.fromisoformat(date_str)

        # Aggregate per product_id to avoid duplicates
        aggregated = defaultdict(lambda: {"quantity": 0, "unit_price": None})

        for pid, qty, price, margin in zip(product_ids, quantities, unit_prices, unit_margins):
            if not pid or int(qty) <= 0:
                continue

            pid = int(pid)
            aggregated[pid]["quantity"] += int(qty)

            # Keep last price or enforce consistency check
            aggregated[pid]["unit_price"] = int(price)
            aggregated[pid]["unit_margin"] = int(margin)

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
        unit_margins = request.form.getlist("unitMargin[]")

        order.created_at = datetime.fromisoformat(date)

        for item in order.items:
            db.session.delete(item)
        db.session.commit()

        for product_id, quantity, unit_price, unit_margin in zip(
                product_ids, quantities, unit_prices, unit_margins
        ):
            if product_id and int(quantity) > 0:
                product = next((p for p in products if p.id == int(product_id)), None)
                if product:
                    order.add_product(
                        product=product, quantity=int(quantity), unit_price=unit_price, unit_margin=unit_margin
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
