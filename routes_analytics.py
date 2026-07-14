from flask import Blueprint, jsonify
from sqlalchemy import func
from models import db, Transaction, Customer, Item

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/api/analytics")


@analytics_bp.route("/summary", methods=["GET"])
def summary():
    txns = Transaction.query.all()

    total_revenue = sum(t.sale_price_at_time * t.qty for t in txns)
    total_profit = sum((t.sale_price_at_time - t.cost_price_at_time) * t.qty for t in txns)
    total_stock_sold = sum(t.qty for t in txns)

    return jsonify({
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "total_stock_sold": total_stock_sold,
        "total_transactions": len(txns),
    })


@analytics_bp.route("/by-customer", methods=["GET"])
def by_customer():
    results = (
        db.session.query(
            Customer.id,
            Customer.name,
            func.sum(Transaction.qty).label("total_qty"),
            func.sum(Transaction.sale_price_at_time * Transaction.qty).label("revenue"),
            func.sum((Transaction.sale_price_at_time - Transaction.cost_price_at_time) * Transaction.qty).label("profit"),
        )
        .join(Transaction, Transaction.customer_id == Customer.id)
        .group_by(Customer.id, Customer.name)
        .order_by(func.sum(Transaction.sale_price_at_time * Transaction.qty).desc())
        .all()
    )

    return jsonify([
        {
            "customer": r.name,
            "total_qty": r.total_qty,
            "revenue": round(r.revenue, 2),
            "profit": round(r.profit, 2),
        }
        for r in results
    ])


@analytics_bp.route("/by-item", methods=["GET"])
def by_item():
    results = (
        db.session.query(
            Item.id,
            Item.name,
            func.sum(Transaction.qty).label("total_qty"),
            func.sum(Transaction.sale_price_at_time * Transaction.qty).label("revenue"),
        )
        .join(Transaction, Transaction.item_id == Item.id)
        .group_by(Item.id, Item.name)
        .order_by(func.sum(Transaction.qty).desc())
        .all()
    )

    return jsonify([
        {"item": r.name, "total_qty": r.total_qty, "revenue": round(r.revenue, 2)}
        for r in results
    ])


@analytics_bp.route("/monthly", methods=["GET"])
def monthly():
    results = (
        db.session.query(
            func.to_char(Transaction.date, "YYYY-MM").label("month"),
            func.sum(Transaction.sale_price_at_time * Transaction.qty).label("revenue"),
        )
        .group_by(func.to_char(Transaction.date, "YYYY-MM"))
        .order_by(func.to_char(Transaction.date, "YYYY-MM"))
        .all()
    )

    return jsonify([{"month": r.month, "revenue": round(r.revenue, 2)} for r in results])
