from flask import Blueprint, request, jsonify
from models import db, Item, StockLog
from auth import login_required, current_user_id

item_bp = Blueprint("item_bp", __name__, url_prefix="/api/items")


@item_bp.route("", methods=["POST"])
@login_required
def add_item():
    data = request.get_json()

    if not data.get("name") or data.get("cost_price") is None or data.get("sale_price") is None:
        return jsonify({"error": "name, cost_price, sale_price required"}), 400

    item = Item(
        user_id=current_user_id(),
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


@item_bp.route("", methods=["GET"])
@login_required
def get_items():
    items = Item.query.filter_by(user_id=current_user_id()).all()
    return jsonify([i.to_dict() for i in items])


@item_bp.route("/<int:item_id>", methods=["GET"])
@login_required
def get_item(item_id):
    item = Item.query.filter_by(id=item_id, user_id=current_user_id()).first()
    if not item:
        return jsonify({"error": "item not found"}), 404
    return jsonify(item.to_dict())


@item_bp.route("/<int:item_id>", methods=["PUT"])
@login_required
def update_item(item_id):
    item = Item.query.filter_by(id=item_id, user_id=current_user_id()).first()
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


@item_bp.route("/<int:item_id>/stock", methods=["POST"])
@login_required
def adjust_stock(item_id):
    item = Item.query.filter_by(id=item_id, user_id=current_user_id()).first()
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


@item_bp.route("/<int:item_id>", methods=["DELETE"])
@login_required
def delete_item(item_id):
    item = Item.query.filter_by(id=item_id, user_id=current_user_id()).first()
    if not item:
        return jsonify({"error": "item not found"}), 404

    StockLog.query.filter_by(item_id=item_id).delete()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "item deleted"})
