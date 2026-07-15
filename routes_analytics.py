from flask import Blueprint, jsonify
from sqlalchemy import func, text
from models import db, Transaction, Customer, Item
from auth import login_required, current_user_id

analytics_bp = Blueprint("analytics_bp", __name__, url_prefix="/api/analytics")


@analytics_bp.route("/summary", methods=["GET"])
@login_required
def summary():
    uid = current_user_id()
    txns = Transaction.query.filter_by(user_id=uid).all()

    total_revenue = sum(t.sale_price_at_time * t.qty for t in txns)
    total_profit = sum((t.sale_price_at_time - t.cost_price_at_time) * t.qty for t in txns)
    total_stock_sold = sum(t.qty for t in txns)
    total_pending = sum((t.sale_price_at_time * t.qty) - t.amount_paid for t in txns)

    return jsonify({
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "total_stock_sold": total_stock_sold,
        "total_transactions": len(txns),
        "total_pending": round(total_pending, 2),
    })


@analytics_bp.route("/by-customer", methods=["GET"])
@login_required
def by_customer():
    uid = current_user_id()
    results = (
        db.session.query(
            Customer.id,
            Customer.name,
            func.sum(Transaction.qty).label("total_qty"),
            func.sum(Transaction.sale_price_at_time * Transaction.qty).label("revenue"),
            func.sum((Transaction.sale_price_at_time - Transaction.cost_price_at_time) * Transaction.qty).label("profit"),
            func.sum(Transaction.amount_paid).label("paid"),
        )
        .join(Transaction, Transaction.customer_id == Customer.id)
        .filter(Customer.user_id == uid, Transaction.user_id == uid)
        .group_by(Customer.id, Customer.name)
        .order_by(func.sum(Transaction.sale_price_at_time * Transaction.qty).desc())
        .all()
    )

    return jsonify([
        {
            "id": r.id,
            "customer": r.name,
            "total_qty": r.total_qty,
            "revenue": round(r.revenue, 2),
            "profit": round(r.profit, 2),
            "pending": round(r.revenue - r.paid, 2),
        }
        for r in results
    ])


@analytics_bp.route("/by-item", methods=["GET"])
@login_required
def by_item():
    uid = current_user_id()
    results = (
        db.session.query(
            Item.id,
            Item.name,
            func.sum(Transaction.qty).label("total_qty"),
            func.sum(Transaction.sale_price_at_time * Transaction.qty).label("revenue"),
        )
        .join(Transaction, Transaction.item_id == Item.id)
        .filter(Item.user_id == uid, Transaction.user_id == uid)
        .group_by(Item.id, Item.name)
        .order_by(func.sum(Transaction.qty).desc())
        .all()
    )

    return jsonify([
        {"item": r.name, "total_qty": r.total_qty, "revenue": round(r.revenue, 2)}
        for r in results
    ])


@analytics_bp.route("/monthly", methods=["GET"])
@login_required
def monthly():
    uid = current_user_id()
    results = (
        db.session.query(
            func.to_char(Transaction.date, "YYYY-MM").label("month"),
            func.sum(Transaction.sale_price_at_time * Transaction.qty).label("revenue"),
            func.sum((Transaction.sale_price_at_time - Transaction.cost_price_at_time) * Transaction.qty).label("profit"),
            func.sum(Transaction.qty).label("qty"),
        )
        .filter(Transaction.user_id == uid)
        .group_by(text("1"))
        .order_by(text("1"))
        .all()
    )

    return jsonify([
        {"month": r.month, "revenue": round(r.revenue, 2), "profit": round(r.profit, 2), "qty": r.qty}
        for r in results
    ])


@analytics_bp.route("/snapshot", methods=["GET"])
@login_required
def snapshot():
    uid = current_user_id()
    txns = Transaction.query.filter_by(user_id=uid).all()
    total_customers = Customer.query.filter_by(user_id=uid).count()
    total_items = Item.query.filter_by(user_id=uid).count()
    low_stock_count = Item.query.filter(
        Item.user_id == uid, Item.current_stock <= Item.reorder_threshold
    ).count()

    avg_order_value = 0
    if txns:
        avg_order_value = sum(t.sale_price_at_time * t.qty for t in txns) / len(txns)

    top_customer_row = (
        db.session.query(Customer.name, func.sum(Transaction.sale_price_at_time * Transaction.qty).label("revenue"))
        .join(Transaction, Transaction.customer_id == Customer.id)
        .filter(Customer.user_id == uid, Transaction.user_id == uid)
        .group_by(Customer.name)
        .order_by(func.sum(Transaction.sale_price_at_time * Transaction.qty).desc())
        .first()
    )
    top_item_row = (
        db.session.query(Item.name, func.sum(Transaction.qty).label("qty"))
        .join(Transaction, Transaction.item_id == Item.id)
        .filter(Item.user_id == uid, Transaction.user_id == uid)
        .group_by(Item.name)
        .order_by(func.sum(Transaction.qty).desc())
        .first()
    )

    return jsonify({
        "total_customers": total_customers,
        "total_items": total_items,
        "low_stock_count": low_stock_count,
        "avg_order_value": round(avg_order_value, 2),
        "top_customer": top_customer_row.name if top_customer_row else "—",
        "top_item": top_item_row.name if top_item_row else "—",
    })
