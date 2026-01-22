from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required
from sqlalchemy import desc, asc, func, distinct, case
from sqlalchemy.orm import selectinload
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from . import order
from .. import normalize_text
from ..extensions import db
from ..models import Order, OrderItem, Product


@order.route("/unit_names", methods=["GET"])
@login_required
def order_unit_names():
    term = request.args.get("term", "", type=str).strip()
    term_norm = normalize_text(term)

    start = request.args.get("start", "", type=str).strip()
    end = request.args.get("end", "", type=str).strip()
    order_id = request.args.get("order_id", "", type=str).strip()

    selected = request.args.getlist("selected[]") or request.args.getlist("selected")
    selected_norm = sorted({normalize_text(x) for x in selected if normalize_text(x)})

    base = (
        db.session.query(OrderItem.unit_name, OrderItem.unit_name_search)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(OrderItem.unit_name_search.isnot(None))
    )

    # optional scope filters for suggestions
    if order_id and order_id.isdigit():
        base = base.filter(Order.id == int(order_id))

    if start:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        base = base.filter(Order.created_at >= start_dt)

    if end:
        end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
        base = base.filter(Order.created_at < end_dt)

    # if already selected: only suggest compatible options + exclude selected
    if selected_norm:
        orders_with_all_selected = (
            db.session.query(OrderItem.order_id)
            .filter(OrderItem.unit_name_search.in_(selected_norm))
            .group_by(OrderItem.order_id)
            .having(func.count(distinct(OrderItem.unit_name_search)) == len(selected_norm))
            .subquery()
        )
        base = base.filter(OrderItem.order_id.in_(orders_with_all_selected))
        base = base.filter(~OrderItem.unit_name_search.in_(selected_norm))

    if term_norm:
        base = base.filter(OrderItem.unit_name_search.contains(term_norm))

    rows = (
        base.group_by(OrderItem.unit_name, OrderItem.unit_name_search)
        .order_by(OrderItem.unit_name)
        .limit(20)
        .all()
    )

    items = [name for name, _ in rows if name]
    return jsonify({
        "results": [{"id": name, "text": name} for name in items],
        "items": items
    })


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

    unit_names = request.args.getlist("unit_names")  # selected display strings
    sort = request.args.get("sort", "created_at", type=str)
    direction = request.args.get("direction", "desc", type=str)

    # Normalize selected unit names (for AND semantics)
    selected_norm = sorted({normalize_text(n) for n in unit_names if normalize_text(n)})

    oi = OrderItem  # alias convenience

    # Aggregate totals (SQL)
    total_price_expr = func.coalesce(func.sum(oi.quantity * oi.unit_price), 0).label("total_price")
    total_margin_expr = func.coalesce(func.sum(oi.quantity * oi.unit_margin), 0).label("total_margin")
    grand_total_expr = (total_price_expr + total_margin_expr).label("grand_total")

    # Base query: Order + aggregates
    query = (
        db.session.query(Order)
        .options(selectinload(Order.items))
        .outerjoin(oi)
        .group_by(Order.id)
    )

    # Order-level filters
    if order_id and order_id.isdigit():
        query = query.filter(Order.id == int(order_id))

    if start:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        query = query.filter(Order.created_at >= start_dt)

    if end:
        end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Order.created_at < end_dt)

    # AND filter: order must contain ALL selected unit_names (case-insensitive via unit_name_search)
    if selected_norm:
        matched_distinct_expr = func.count(
            distinct(
                case(
                    (oi.unit_name_search.in_(selected_norm), oi.unit_name_search),
                    else_=None,
                )
            )
        )
        query = query.having(matched_distinct_expr == len(selected_norm))

    # Sorting whitelist (add totals)
    sort_map = {
        "id": Order.id,
        "created_at": Order.created_at,
        "total_price": total_price_expr,
        "total_margin": total_margin_expr,
        "grand_total": grand_total_expr,
    }
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
            "unit_names": unit_names,
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
            return "Date is required", 400

        try:
            created_at = datetime.fromisoformat(date_str)
        except ValueError:
            return "Invalid date format", 400

        product_ids = request.form.getlist("product[]")
        quantities = request.form.getlist("quantity[]")
        unit_prices = request.form.getlist("unitPrice[]")
        unit_margins = request.form.getlist("unitMargin[]")

        # Basic shape check so we don't silently lose rows via zip truncation
        n = len(product_ids)
        if not (len(quantities) == len(unit_prices) == len(unit_margins) == n):
            return "Invalid order payload (row lengths mismatch)", 400

        aggregated = defaultdict(lambda: {"quantity": 0, "unit_price": None, "unit_margin": None})

        for pid, qty, price, margin in zip(product_ids, quantities, unit_prices, unit_margins):
            if not pid:
                continue

            try:
                pid_int = int(pid)
                qty_int = int(qty)
            except (TypeError, ValueError):
                return "Invalid product or quantity", 400

            if qty_int <= 0:
                continue

            # Parse money values safely (allow empty -> None or treat as 0; choose your rule)
            try:
                price_dec = Decimal(price) if price not in (None, "",) else None
                margin_dec = Decimal(margin) if margin not in (None, "",) else None
            except (InvalidOperation, TypeError):
                return "Invalid unit price or margin", 400

            aggregated[pid_int]["quantity"] += qty_int
            # keep last entered values (or enforce consistency if you prefer)
            aggregated[pid_int]["unit_price"] = price_dec
            aggregated[pid_int]["unit_margin"] = margin_dec

        if not aggregated:
            return "Order must contain at least one product", 400

        product_map = {
            p.id: p
            for p in Product.query.filter(Product.id.in_(aggregated.keys())).all()
        }

        new_order = Order(created_at=created_at)

        for pid, data in aggregated.items():
            product = product_map.get(pid)
            if not product:
                continue

            # Decide defaults if user left blank
            unit_price = data["unit_price"] if data["unit_price"] is not None else Decimal("0")
            unit_margin = data["unit_margin"] if data["unit_margin"] is not None else Decimal("0")

            new_order.add_product(
                product=product,
                quantity=data["quantity"],
                unit_price=unit_price,
                unit_margin=unit_margin,  # make sure add_product accepts this
                unit_name=product.name
            )

        db.session.add(new_order)
        db.session.commit()
        return redirect(url_for("order.orders_list"))

    return render_template("order/add.html", products=products)




def _safe_get(lst, i, default=""):
    return lst[i] if i < len(lst) else default

@order.route("/edit/<int:order_id>", methods=["GET", "POST"])
@login_required
def edit_order(order_id):
    order: Order = Order.query.get_or_404(order_id)
    products = Product.query.order_by(Product.name).all()
    product_by_id = {p.id: p for p in products}

    if request.method == "POST":
        date_str = request.form.get("date")
        if not date_str:
            return 400, "Date is required"

        try:
            new_created_at = datetime.fromisoformat(date_str)
        except ValueError:
            return 400, "Invalid date format"

        product_ids = request.form.getlist("product[]")
        quantities = request.form.getlist("quantity[]")
        unit_prices = request.form.getlist("unitPrice[]")
        unit_margins = request.form.getlist("unitMargin[]")

        aggregated = defaultdict(lambda: {"quantity": 0, "unit_price": None, "unit_margin": None})

        for i in range(len(product_ids)):
            pid = _safe_get(product_ids, i)
            qty = _safe_get(quantities, i)
            price = _safe_get(unit_prices, i)
            margin = _safe_get(unit_margins, i)

            if not pid:
                continue

            try:
                pid_int = int(pid)
                qty_int = int(qty) if qty not in ("", None) else 0
            except ValueError:
                continue

            if qty_int <= 0:
                continue

            try:
                price_val = Decimal(price) if price not in ("", None) else Decimal("0")
            except ValueError:
                price_val = Decimal("0")

            try:
                margin_val = Decimal(margin) if margin not in ("", None) else Decimal("0")
            except (InvalidOperation, ValueError):
                margin_val = Decimal("0")

            aggregated[pid_int]["quantity"] += qty_int
            aggregated[pid_int]["unit_price"] = price_val
            aggregated[pid_int]["unit_margin"] = margin_val

        submitted_pids = set(aggregated.keys())
        existing_by_pid = {item.product_id: item for item in order.items}

        try:
            with db.session.begin_nested():
                order.created_at = new_created_at

                # 2) UPSERT
                for pid_int, data in aggregated.items():
                    product = product_by_id.get(pid_int)
                    if not product:
                        continue

                    item = existing_by_pid.get(pid_int)
                    if item:
                        item.quantity = data["quantity"]
                        item.unit_price = data["unit_price"]
                        item.unit_margin = data["unit_margin"]
                    else:
                        order.add_product(
                            product=product,
                            quantity=data["quantity"],
                            unit_price=data["unit_price"],
                            unit_margin=data["unit_margin"],
                            unit_name=product.name
                        )

                # 3) PRUNE removed items
                for pid_int, item in existing_by_pid.items():
                    if pid_int not in submitted_pids:
                        db.session.delete(item)

            # IMPORTANT: finalize outer transaction
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

        return redirect(url_for("order.orders_list"))

    return render_template("order/edit.html", products=products, order=order)


@login_required
@order.route("/delete_order/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    order: Order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return {"order_id": order_id, "status": "success"}, 200
