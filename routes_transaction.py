from flask import Blueprint, request, jsonify
from models import db, Transaction, Item, Customer, StockLog

transaction_bp = Blueprint("transaction_bp", __name__, url_prefix="/api/transactions")


# CREATE (record a sale)
@transaction_bp.route("", methods=["POST"])
def add_transaction():
    data = request.get_json()

    customer_id = data.get("customer_id")
    item_id = data.get("item_id")
    qty = data.get("qty")

    if not customer_id or not item_id or not qty:
        return jsonify({"error": "customer_id, item_id, qty required"}), 400

    customer = Customer.query.get(customer_id)
    item = Item.query.get(item_id)

    if not customer:
        return jsonify({"error": "customer not found"}), 404
    if not item:
        return jsonify({"error": "item not found"}), 404

    if item.current_stock < qty:
        return jsonify({"error": f"insufficient stock, only {item.current_stock} left"}), 400

    # deduct stock
    item.current_stock -= qty
    db.session.add(StockLog(item_id=item.id, change_qty=-qty, reason="sale"))

    # record transaction with prices locked at time of sale
    txn = Transaction(
        customer_id=customer_id,
        item_id=item_id,
        qty=qty,
        sale_price_at_time=item.sale_price,
        cost_price_at_time=item.cost_price,
    )
    db.session.add(txn)
    db.session.commit()

    return jsonify({
        "id": txn.id,
        "customer": customer.name,
        "item": item.name,
        "qty": qty,
        "sale_price": txn.sale_price_at_time,
        "total": round(txn.sale_price_at_time * qty, 2),
        "profit": round((txn.sale_price_at_time - txn.cost_price_at_time) * qty, 2),
        "remaining_stock": item.current_stock,
    }), 201


# READ ALL (transaction history)
@transaction_bp.route("", methods=["GET"])
def get_transactions():
    txns = Transaction.query.order_by(Transaction.date.desc()).all()
    result = []
    for t in txns:
        result.append({
            "id": t.id,
            "customer": t.customer.name,
            "item": t.item.name,
            "qty": t.qty,
            "sale_price": t.sale_price_at_time,
            "total": round(t.sale_price_at_time * t.qty, 2),
            "profit": round((t.sale_price_at_time - t.cost_price_at_time) * t.qty, 2),
            "date": t.date.strftime("%Y-%m-%d %H:%M"),
        })
    return jsonify(result)


# DELETE (undo a sale — restores stock)
@transaction_bp.route("/<int:txn_id>", methods=["DELETE"])
def delete_transaction(txn_id):
    txn = Transaction.query.get(txn_id)
    if not txn:
        return jsonify({"error": "transaction not found"}), 404

    item = Item.query.get(txn.item_id)
    if item:
        item.current_stock += txn.qty
        db.session.add(StockLog(item_id=item.id, change_qty=txn.qty, reason="sale reversed"))

    db.session.delete(txn)
    db.session.commit()
    return jsonify({"message": "transaction deleted, stock restored"})
