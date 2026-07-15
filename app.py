from datetime import timedelta
from flask import Flask, render_template, redirect, session
from config import Config
from models import db
from routes_customer import customer_bp
from routes_item import item_bp
from routes_transaction import transaction_bp
from routes_analytics import analytics_bp
from routes_email import email_bp
from routes_reports import reports_bp
from routes_auth import auth_bp
from routes_assistant import assistant_bp
from auth import login_required


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # session lasts 30 days, does not expire just from browser closing
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True

    db.init_app(app)

    app.register_blueprint(customer_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(assistant_bp)

    @app.route("/")
    def health():
        if "user_id" in session:
            return redirect("/dashboard")
        return redirect("/login")

    @app.route("/login")
    def login_page():
        if "user_id" in session:
            return redirect("/dashboard")
        return render_template("login.html")

    @app.route("/signup")
    def signup_page():
        if "user_id" in session:
            return redirect("/dashboard")
        return render_template("signup.html")

    @app.route("/profile")
    @login_required
    def profile_page():
        return render_template("profile.html", active="profile")

    @app.route("/customers")
    @login_required
    def customers_page():
        return render_template("customers.html", active="customers")

    @app.route("/customers/<int:customer_id>")
    @login_required
    def customer_detail_page(customer_id):
        return render_template("customer_detail.html", active="customers", customer_id=customer_id)

    @app.route("/items")
    @login_required
    def items_page():
        return render_template("items.html", active="items")

    @app.route("/sales")
    @login_required
    def sales_page():
        return render_template("sales.html", active="sales")

    @app.route("/dashboard")
    @login_required
    def dashboard_page():
        return render_template("dashboard.html", active="dashboard")

    @app.route("/reports")
    @login_required
    def reports_page():
        return render_template("reports.html", active="reports")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
