from flask import Blueprint, request, jsonify
from models import db, Item, StockLog

item_bp = Blueprint("item_bp", __name__, url_prefix="/api/items")


# CREATE
@item_bp.route("", methods=["POST"])
def add_item():
    data = request.get_json()

    if not data.get("name") or data.get("cost_price") is None or data.get("sale_price") is None:
        return jsonify({"error": "name, cost_price, sale_price required"}), 400

    item = Item(
        name=data["name"],
        cost_price=data["cost_price"],
        sale_price=data["sale_price"],
        current_stock=data.get("current_stock", 0),
        reorder_threshold=data.get("reorder_threshold", 10),
        supplier_email=data.get("supplier_email"),
    )
    db.session.add(item)
    db.session.commit()

    if item.current_stock > 0:
        db.session.add(StockLog(item_id=item.id, change_qty=item.current_stock, reason="restock"))
        db.session.commit()

    return jsonify(item.to_dict()), 201


# READ ALL
@item_bp.route("", methods=["GET"])
def get_items():
    items = Item.query.all()
    return jsonify([i.to_dict() for i in items])


# READ ONE
@item_bp.route("/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "item not found"}), 404
    return jsonify(item.to_dict())


# UPDATE (details/price)
@item_bp.route("/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "item not found"}), 404

    data = request.get_json()
    item.name = data.get("name", item.name)
    item.cost_price = data.get("cost_price", item.cost_price)
    item.sale_price = data.get("sale_price", item.sale_price)
    item.reorder_threshold = data.get("reorder_threshold", item.reorder_threshold)
    item.supplier_email = data.get("supplier_email", item.supplier_email)

    db.session.commit()
    return jsonify(item.to_dict())


# ADJUST STOCK (add or deduct, logged)
@item_bp.route("/<int:item_id>/stock", methods=["POST"])
def adjust_stock(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "item not found"}), 404

    data = request.get_json()
    change = data.get("change_qty")
    reason = data.get("reason", "manual")

    if change is None:
        return jsonify({"error": "change_qty required (positive to add, negative to deduct)"}), 400

    new_stock = item.current_stock + change
    if new_stock < 0:
        return jsonify({"error": "insufficient stock"}), 400

    item.current_stock = new_stock
    db.session.add(StockLog(item_id=item.id, change_qty=change, reason=reason))
    db.session.commit()

    return jsonify(item.to_dict())


# DELETE
@item_bp.route("/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "item not found"}), 404

    StockLog.query.filter_by(item_id=item_id).delete()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "item deleted"})
