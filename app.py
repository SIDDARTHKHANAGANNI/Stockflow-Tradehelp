from flask import Flask, jsonify, render_template
from config import Config
from models import db
from routes_customer import customer_bp
from routes_item import item_bp
from routes_transaction import transaction_bp
from routes_analytics import analytics_bp
from routes_email import email_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    app.register_blueprint(customer_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(email_bp)

    @app.route("/")
    def health():
        return jsonify({"status": "StockFlow running"})

    @app.route("/customers")
    def customers_page():
        return render_template("customers.html", active="customers")

    @app.route("/items")
    def items_page():
        return render_template("items.html", active="items")

    @app.route("/sales")
    def sales_page():
        return render_template("sales.html", active="sales")

    @app.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html", active="dashboard")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
