"""
Run once to create all tables in your Neon Postgres DB.
Usage: python init_db.py
"""
from app import create_app
from models import db

app = create_app()

with app.app_context():
    db.create_all()
    print("Tables created successfully.")
