from flask import Blueprint, request, jsonify
from models import db, Customer
from auth import login_required, current_user_id

customer_bp = Blueprint("customer_bp", __name__, url_prefix="/api/customers")


@customer_bp.route("", methods=["POST"])
@login_required
def add_customer():
    data = request.get_json()

    if not data.get("name") or not data.get("phone"):
        return jsonify({"error": "name and phone required"}), 400

    customer = Customer(
        user_id=current_user_id(),
        name=data["name"],
        phone=data["phone"],
        address=data.get("address"),
        lat=data.get("lat"),
        lng=data.get("lng"),
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify(customer.to_dict()), 201


@customer_bp.route("", methods=["GET"])
@login_required
def get_customers():
    customers = Customer.query.filter_by(user_id=current_user_id()).all()
    return jsonify([c.to_dict() for c in customers])


@customer_bp.route("/<int:customer_id>", methods=["GET"])
@login_required
def get_customer(customer_id):
    customer = Customer.query.filter_by(id=customer_id, user_id=current_user_id()).first()
    if not customer:
        return jsonify({"error": "customer not found"}), 404
    return jsonify(customer.to_dict())


@customer_bp.route("/<int:customer_id>", methods=["PUT"])
@login_required
def update_customer(customer_id):
    customer = Customer.query.filter_by(id=customer_id, user_id=current_user_id()).first()
    if not customer:
        return jsonify({"error": "customer not found"}), 404

    data = request.get_json()
    customer.name = data.get("name", customer.name)
    customer.phone = data.get("phone", customer.phone)
    customer.address = data.get("address", customer.address)
    customer.lat = data.get("lat", customer.lat)
    customer.lng = data.get("lng", customer.lng)

    db.session.commit()
    return jsonify(customer.to_dict())


@customer_bp.route("/<int:customer_id>", methods=["DELETE"])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.filter_by(id=customer_id, user_id=current_user_id()).first()
    if not customer:
        return jsonify({"error": "customer not found"}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "customer deleted"})
