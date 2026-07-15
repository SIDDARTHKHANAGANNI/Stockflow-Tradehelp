from flask import Blueprint, request, jsonify
from models import db, Transaction, Item, Customer, StockLog
from auth import login_required, current_user_id

transaction_bp = Blueprint("transaction_bp", __name__, url_prefix="/api/transactions")


@transaction_bp.route("", methods=["POST"])
@login_required
def add_transaction():
    uid = current_user_id()
    data = request.get_json()

    customer_id = data.get("customer_id")
    item_id = data.get("item_id")
    qty = data.get("qty")
    amount_paid = data.get("amount_paid", 0)

    if not customer_id or not item_id or not qty:
        return jsonify({"error": "customer_id, item_id, qty required"}), 400

    customer = Customer.query.filter_by(id=customer_id, user_id=uid).first()
    item = Item.query.filter_by(id=item_id, user_id=uid).first()

    if not customer:
        return jsonify({"error": "customer not found"}), 404
    if not item:
        return jsonify({"error": "item not found"}), 404

    if item.current_stock < qty:
        return jsonify({"error": f"insufficient stock, only {item.current_stock} left"}), 400

    total = item.sale_price * qty
    if amount_paid > total:
        return jsonify({"error": "amount paid cannot exceed total"}), 400

    item.current_stock -= qty
    db.session.add(StockLog(item_id=item.id, change_qty=-qty, reason="sale"))

    txn = Transaction(
        user_id=uid,
        customer_id=customer_id,
        item_id=item_id,
        qty=qty,
        sale_price_at_time=item.sale_price,
        cost_price_at_time=item.cost_price,
        amount_paid=amount_paid,
    )
    db.session.add(txn)
    db.session.commit()

    return jsonify({
        "id": txn.id,
        "customer": customer.name,
        "item": item.name,
        "qty": qty,
        "sale_price": txn.sale_price_at_time,
        "total": round(total, 2),
        "amount_paid": round(amount_paid, 2),
        "pending": round(total - amount_paid, 2),
        "profit": round((txn.sale_price_at_time - txn.cost_price_at_time) * qty, 2),
        "remaining_stock": item.current_stock,
    }), 201


@transaction_bp.route("", methods=["GET"])
@login_required
def get_transactions():
    txns = Transaction.query.filter_by(user_id=current_user_id()).order_by(Transaction.date.desc()).all()
    result = []
    for t in txns:
        total = t.sale_price_at_time * t.qty
        result.append({
            "id": t.id,
            "customer_id": t.customer_id,
            "customer": t.customer.name,
            "item": t.item.name,
            "qty": t.qty,
            "sale_price": t.sale_price_at_time,
            "total": round(total, 2),
            "amount_paid": round(t.amount_paid, 2),
            "pending": round(total - t.amount_paid, 2),
            "profit": round((t.sale_price_at_time - t.cost_price_at_time) * t.qty, 2),
            "date": t.date.strftime("%Y-%m-%d %H:%M"),
        })
    return jsonify(result)


@transaction_bp.route("/<int:txn_id>/payment", methods=["PUT"])
@login_required
def update_payment(txn_id):
    txn = Transaction.query.filter_by(id=txn_id, user_id=current_user_id()).first()
    if not txn:
        return jsonify({"error": "transaction not found"}), 404

    data = request.get_json()
    new_paid = data.get("amount_paid")
    if new_paid is None:
        return jsonify({"error": "amount_paid required"}), 400

    total = txn.sale_price_at_time * txn.qty
    if new_paid < 0 or new_paid > total:
        return jsonify({"error": f"amount_paid must be between 0 and {total}"}), 400

    txn.amount_paid = new_paid
    db.session.commit()

    return jsonify({
        "id": txn.id,
        "total": round(total, 2),
        "amount_paid": round(txn.amount_paid, 2),
        "pending": round(total - txn.amount_paid, 2),
    })


@transaction_bp.route("/<int:txn_id>", methods=["DELETE"])
@login_required
def delete_transaction(txn_id):
    txn = Transaction.query.filter_by(id=txn_id, user_id=current_user_id()).first()
    if not txn:
        return jsonify({"error": "transaction not found"}), 404

    item = Item.query.get(txn.item_id)
    if item:
        item.current_stock += txn.qty
        db.session.add(StockLog(item_id=item.id, change_qty=txn.qty, reason="sale reversed"))

    db.session.delete(txn)
    db.session.commit()
    return jsonify({"message": "transaction deleted, stock restored"})


@transaction_bp.route("/customer-summary/<int:customer_id>", methods=["GET"])
@login_required
def customer_summary(customer_id):
    uid = current_user_id()
    customer = Customer.query.filter_by(id=customer_id, user_id=uid).first()
    if not customer:
        return jsonify({"error": "customer not found"}), 404

    txns = (
        Transaction.query.filter_by(customer_id=customer_id, user_id=uid)
        .order_by(Transaction.date.desc())
        .all()
    )

    history = []
    monthly_map = {}
    total_revenue = 0
    total_profit = 0
    total_pending = 0

    for t in txns:
        total = t.sale_price_at_time * t.qty
        profit = (t.sale_price_at_time - t.cost_price_at_time) * t.qty
        pending = total - t.amount_paid

        total_revenue += total
        total_profit += profit
        total_pending += pending

        history.append({
            "id": t.id,
            "item": t.item.name,
            "qty": t.qty,
            "total": round(total, 2),
            "amount_paid": round(t.amount_paid, 2),
            "pending": round(pending, 2),
            "date": t.date.strftime("%Y-%m-%d %H:%M"),
        })

        month_key = t.date.strftime("%Y-%m")
        if month_key not in monthly_map:
            monthly_map[month_key] = {"revenue": 0, "profit": 0}
        monthly_map[month_key]["revenue"] += total
        monthly_map[month_key]["profit"] += profit

    monthly = [
        {"month": k, "revenue": round(v["revenue"], 2), "profit": round(v["profit"], 2)}
        for k, v in sorted(monthly_map.items())
    ]

    return jsonify({
        "customer": customer.to_dict(),
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "total_pending": round(total_pending, 2),
        "history": history,
        "monthly": monthly,
    })
