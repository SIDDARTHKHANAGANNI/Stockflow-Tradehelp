from flask import Blueprint, request, jsonify, session
from models import db, User, Customer, Item, Transaction, StockLog
from auth import login_required, current_user_id

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = (data.get("username") or "").strip().lower()
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    if len(password) < 4:
        return jsonify({"error": "password must be at least 4 characters"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already taken"}), 409

    user = User(username=username, name=name or username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session.permanent = True
    session["user_id"] = user.id

    return jsonify(user.to_dict()), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid username or password"}), 401

    session.permanent = True
    session["user_id"] = user.id

    return jsonify(user.to_dict())


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "logged out"})


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user = User.query.get(current_user_id())
    if not user:
        session.clear()
        return jsonify({"error": "not authenticated"}), 401
    return jsonify(user.to_dict())


@auth_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    user = User.query.get(current_user_id())
    data = request.get_json()

    new_name = data.get("name")
    new_username = data.get("username")
    new_password = data.get("password")

    if new_username:
        new_username = new_username.strip().lower()
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != user.id:
            return jsonify({"error": "username already taken"}), 409
        user.username = new_username

    if new_name:
        user.name = new_name.strip()

    if new_password:
        if len(new_password) < 4:
            return jsonify({"error": "password must be at least 4 characters"}), 400
        user.set_password(new_password)

    db.session.commit()
    return jsonify(user.to_dict())


@auth_bp.route("/account", methods=["DELETE"])
@login_required
def delete_account():
    uid = current_user_id()

    item_ids = [i.id for i in Item.query.filter_by(user_id=uid).all()]
    if item_ids:
        StockLog.query.filter(StockLog.item_id.in_(item_ids)).delete(synchronize_session=False)

    Transaction.query.filter_by(user_id=uid).delete(synchronize_session=False)
    Item.query.filter_by(user_id=uid).delete(synchronize_session=False)
    Customer.query.filter_by(user_id=uid).delete(synchronize_session=False)
    User.query.filter_by(id=uid).delete(synchronize_session=False)

    db.session.commit()
    session.clear()

    return jsonify({"message": "account and all data deleted"})
