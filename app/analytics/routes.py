from flask import jsonify, render_template, request
from flask_login import login_required
from sqlalchemy import func
from datetime import datetime, date, timedelta
from ..extensions import db
from ..models import Order, Product, SMMStats, OrderItem
from . import analytics


@analytics.route("/stats", methods=["GET"])
@login_required
def stats():
    return render_template("analytics/stats.html")


@analytics.route("/get_monthly_stats", methods=["POST"])
@login_required
def get_monthly_stats():
    data = request.get_json()
    month_param = data.get("month")
    if not month_param:
        return jsonify({"error": "month parameter required"}), 400

    try:
        year, month = map(int, month_param.split("-"))
        first_day = date(year, month, 1)
    except ValueError:
        return jsonify({"error": "Invalid month format"}), 400

    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)

    order_data = (
        db.session.query(
            func.date(Order.created_at).label("day"),
            func.count(Order.id).label("order_count"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_sales"),
            func.sum(
                OrderItem.quantity * OrderItem.unit_price
                - (Product.cost * OrderItem.quantity)
            ).label("total_margin"),
        )
        .join(OrderItem, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(Order.created_at >= first_day, Order.created_at < next_month)
        .group_by(func.date(Order.created_at))
        .all()
    )

    orders_by_day = {
        datetime.strptime(record.day, "%Y-%m-%d").date(): {
            "order_count": record.order_count,
            "total_sales": float(record.total_sales or 0),
            "total_margin": float(record.total_margin or 0),
        }
        for record in order_data
    }

    smm_data = (
        db.session.query(SMMStats)
        .filter(SMMStats.date >= first_day, SMMStats.date < next_month)
        .all()
    )
    smm_by_day = {sd.date: sd for sd in smm_data}

    days = []
    day = first_day

    while day <= last_day:
        order_info = orders_by_day.get(
            day, {"order_count": 0, "total_sales": 0.0, "total_margin": 0.0}
        )
        smm_info = smm_by_day.get(day)

        if smm_info:
            pass

        if day == date(2025, 11, 6):
            pass

        days.append(
            {
                "date": day.isoformat(),
                "order_count": order_info["order_count"],
                "total_sales": order_info["total_sales"],
                "total_margin": order_info["total_margin"],
                "smm_spends": float(smm_info.spends) if smm_info else 0.0,
                "smm_coverage": smm_info.coverage if smm_info else 0,
                "smm_clicks": smm_info.clicks if smm_info else 0,
                "smm_direct_messages": smm_info.direct_messages if smm_info else 0,
                "revenue": order_info["total_margin"] - (float(smm_info.spends) if smm_info else 0.0),
            }
        )

        day += timedelta(days=1)

    return jsonify(days)


@analytics.route("/update_smm_stat", methods=["POST"])
@login_required
def update_smm_stat():
    data = request.get_json()
    field = data.get("type")
    day = data.get("date")
    value = data.get("value")

    if not (day and field and value):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        day_date = datetime.strptime(day, "%Y-%m-%d").date()
        value = float(value)
    except Exception as e:
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400

    stat = SMMStats.query.filter_by(date=day_date).first()
    if not stat:
        stat = SMMStats(date_value=day_date)
        db.session.add(stat)

    if hasattr(stat, field):
        setattr(stat, field, value)
    else:
        return jsonify({"error": f"Invalid field name: {field}"}), 400

    db.session.commit()
    return jsonify({"success": True, "day": day, "field": field, "value": value})

@analytics.route("/summary", methods=["GET", "POST"])
@login_required
def summary():
    if request.method == "POST":
        json = request.get_json()
        startDate = json["startDate"]
        endDate = json["endDate"]
        
        data = (db.session.query(
            func.date(Order.created_at).label("day"),
            func.sum(SMMStats.spends).label("total_spends"),
            func.sum(SMMStats.coverage).label("total_coverage"),
            func.sum(SMMStats.clicks).label("total_clicks"),
            func.count(Order.id).label("total_sales"),
            func.sum(SMMStats.direct_messages).label("total_orders"),
            func.sum(OrderItem.unit_price * OrderItem.quantity).label("sum_sales"),
            func.sum(
                OrderItem.quantity * OrderItem.unit_price
                - (Product.cost * OrderItem.quantity)
            ).label("margin")
            )
            .join(OrderItem, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Order.created_at >= startDate, Order.created_at < endDate)
            .all()
            )
        
        row = data.pop()
        
        
        return jsonify({
            "total_spends": row.total_spends,
            "total_coverage": row.total_coverage,
            "total_clicks": row.total_clicks,
            "total_sales": row.total_sales,
            "sum_sales": row.sum_sales,
            "total_orders" : row.total_orders,
            "margin": row.margin,
            "revenue": row.margin - row.total_spends,
            "convert": ((row.total_sales / row.total_orders ) * 100) if row.total_orders else 0.0,
            "roas": row.total_spends,    
            "order_price_average": row.total_spends, 
        })
    return render_template("analytics/sum.html")
        