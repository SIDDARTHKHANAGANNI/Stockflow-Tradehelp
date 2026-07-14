from flask import Flask, jsonify, render_template
from config import Config
from models import db
from routes_customer import customer_bp
from routes_item import item_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    app.register_blueprint(customer_bp)
    app.register_blueprint(item_bp)

    @app.route("/")
    def health():
        return jsonify({"status": "StockFlow running"})

    @app.route("/customers")
    def customers_page():
        return render_template("customers.html")

    @app.route("/items")
    def items_page():
        return render_template("items.html")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
