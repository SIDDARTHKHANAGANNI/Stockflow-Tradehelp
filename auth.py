from functools import wraps
from flask import session, redirect, jsonify, request


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "not authenticated"}), 401
            return redirect("/login")
        return view_func(*args, **kwargs)
    return wrapped


def current_user_id():
    return session.get("user_id")
