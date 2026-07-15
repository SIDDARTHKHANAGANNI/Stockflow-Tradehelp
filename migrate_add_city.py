"""
Adds a `city` column to the customers table.
Usage: python migrate_add_city.py
"""
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    db.session.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS city VARCHAR(120)"))
    db.session.commit()
    print("Migration complete: city column added to customers.")
