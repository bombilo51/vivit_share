from flask import jsonify, render_template, request
from flask_login import login_required
from sqlalchemy import func
from datetime import datetime, timedelta
from ..extensions import db
from ..models import Order, Product, SMMStats, OrderItem
from . import analytics
from ..utils import get_usd_uah_rate

@analytics.route("/stats", methods=["GET"])
@login_required
def stats():
    return render_template("analytics/stats.html")


@analytics.route("/get_monthly_stats", methods=["POST"])
@login_required
def get_monthly_stats():
    data = request.get_json()
    start_date = data.get("startDate")
    end_date = data.get("endDate")

    if not start_date or not end_date:
        return jsonify({"error": "month parameter required"}), 400

    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    order_data = (
        db.session.query(
            func.date(Order.created_at).label("day"),

            # Count unique orders, not line items
            func.count(func.distinct(Order.id)).label("order_count"),

            # Sum of line-level sales
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_sales"),

            # Sum of line-level margin
            func.sum(
                OrderItem.quantity * (OrderItem.unit_price - Product.cost)
            ).label("total_margin"),
        )
        .join(OrderItem, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(
            Order.created_at >= start_date,
            Order.created_at < end_date,
            # optionally:
            # Order.status == "completed"
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
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
        .filter(SMMStats.date >= start_date, SMMStats.date < end_date)
        .all()
    )
    smm_by_day = {sd.date: sd for sd in smm_data}

    days = []
    day = start_date

    while day <= end_date:
        order_info = orders_by_day.get(
            day, {"order_count": 0, "total_sales": 0.0, "total_margin": 0.0}
        )
        smm_info = smm_by_day.get(day)

        if smm_info and not smm_info.usd_rate:
            smm_info.usd_rate = get_usd_uah_rate(day)
            print(f"Added rate Date : {day} | Rate : {smm_info.usd_rate}")
            db.session.commit()

        days.append(
            {
                "date": day.isoformat(),
                "order_count": order_info["order_count"],
                "total_sales": order_info["total_sales"],
                "total_margin": order_info["total_margin"],
                "smm_spends_usd": float(smm_info.spends) if smm_info else 0.0,
                "smm_spends_uah": float(smm_info.spends) * float(smm_info.usd_rate) if smm_info else 0.0,
                "smm_coverage": smm_info.coverage if smm_info else 0,
                "smm_clicks": smm_info.clicks if smm_info else 0,
                "smm_direct_messages": smm_info.direct_messages if smm_info else 0,
                "revenue": order_info["total_margin"] - (float(smm_info.spends) * float(smm_info.usd_rate) if smm_info else 0.0),
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
    usd_rate = SMMStats.query.filter_by(date=day).first().usd_rate

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
    return jsonify({
        "success": True,
        "day": day,
        "field": field,
        "value": value,
        "usd_rate": usd_rate
    })

@analytics.route("/summary", methods=["GET", "POST"])
@login_required
def summary():
    if request.method == "POST":
        json = request.get_json()
        start_date = json["startDate"]
        end_date = json["endDate"]

        data = (
            db.session.query(
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
                ).label("margin"),
            )
            .join(OrderItem, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .join(SMMStats, SMMStats.order_id == Order.id)  # <-- make sure this condition is correct
            .filter(
                Order.created_at >= start_date,
                Order.created_at < end_date,
            )
            .group_by(func.date(Order.created_at))  # <-- required for the aggregates
            .order_by(func.date(Order.created_at))  # <-- optional but usually desirable
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
        