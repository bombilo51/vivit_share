from flask import jsonify, render_template, request, send_file
from flask_login import login_required
from openpyxl.styles.builtins import output
from sqlalchemy import func
from datetime import datetime, timedelta

from .utils import build_excel_data, build_monthly_stats_days
from ..extensions import db
from ..models import Order, Product, SMMStats, OrderItem
from . import analytics
from ..utils.db import get_usd_uah_rate


@analytics.route("/stats", methods=["GET"])
@login_required
def stats():
    return render_template("analytics/stats.html")

@analytics.route("/get_monthly_stats_html", methods=["POST"])
@login_required
def get_monthly_stats_html():
    data = request.get_json() or {}
    start_date = data.get("startDate")
    end_date = data.get("endDate")

    if not start_date or not end_date:
        return jsonify({"error": "startDate/endDate required"}), 400

    days = build_monthly_stats_days(start_date, end_date)

    html = render_template("analytics/_monthly_stats_tbody.html", data=days)
    return jsonify({"html": html, "data": days})

@analytics.route("/get_monthly_stats", methods=["POST"])
@login_required
def get_monthly_stats():
    data = request.get_json() or {}
    start_date = data.get("startDate")
    end_date = data.get("endDate")

    if not start_date or not end_date:
        return jsonify({"error": "startDate/endDate required"}), 400

    days = build_monthly_stats_days(start_date, end_date)
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
        usd_rate = get_usd_uah_rate(day_date)
        stat.usd_rate = usd_rate
        db.session.add(stat)
    else:
        usd_rate = SMMStats.query.filter_by(date=day_date).first().usd_rate
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
        start_date_row = json["startDate"]
        end_date_row = json["endDate"]

        start_date = datetime.strptime(start_date_row, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = (datetime.strptime(end_date_row, "%Y-%m-%d") + timedelta(days=1)).replace(hour=0, minute=0, second=0,
                                                                                             microsecond=0)

        order = (
            db.session.query(
                func.count(func.distinct(Order.id)).label("total_sales"),
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("sum_sales"),
            )
            .join(OrderItem, Order.id == OrderItem.order_id)
            .filter(Order.created_at >= start_date, Order.created_at < end_date)
            .one()
        )

        smm = (
            db.session.query(
                func.coalesce(func.sum(SMMStats.spends), 0).label("total_spends"),
                func.coalesce(func.sum(SMMStats.coverage), 0).label("total_coverage"),
                func.coalesce(func.sum(SMMStats.clicks), 0).label("total_clicks"),
                func.coalesce(func.sum(SMMStats.direct_messages), 0).label("total_orders"),
                func.coalesce(
                    func.sum(SMMStats.spends * SMMStats.usd_rate),
                    0
                ).label("total_spends_uah"),
            )
            .filter(
                SMMStats.date >= start_date,
                SMMStats.date <= end_date,
            )
            .one()
        )

        if not order or not smm:
            return jsonify({
                "status": "error",
                "error": "Bad data provided"
            })

        return jsonify({
            "status": "success",
            "total_spends": smm.total_spends_uah,
            "total_coverage": smm.total_coverage,
            "total_clicks": smm.total_clicks,
            "total_sales": order.total_sales,
            "sum_sales": order.sum_sales,
            "total_orders": smm.total_orders,
            # "margin": order.margin,
            # "revenue": order.margin - smm.total_spends,
            "convert": ((order.total_sales / smm.total_orders) * 100) if smm.total_orders else 0.0,
            "roas": smm.total_spends,
            "order_price_average": smm.total_spends,
        })
    return render_template("analytics/sum.html")

@analytics.route("/export_monthly_stats_xlsx", methods=["POST"])
@login_required
def export_monthly_stats_xlsx():
    data = request.get_json() or {}
    start_date = data.get("startDate")
    end_date = data.get("endDate")

    if not start_date or not end_date:
        return jsonify({"error": "startDate/endDate required"}), 400

    days = build_monthly_stats_days(start_date, end_date)

    output = build_excel_data(days)

    filename = f"monthly_stats_{start_date}_to_{end_date}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )