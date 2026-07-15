"""
One-time migration: adds amount_paid column to existing transactions table,
and backfills it as fully paid for all past transactions.
Usage: python migrate_add_payment.py
"""
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    db.session.execute(text(
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS amount_paid FLOAT DEFAULT 0"
    ))
    db.session.execute(text(
        "UPDATE transactions SET amount_paid = sale_price_at_time * qty WHERE amount_paid = 0"
    ))
    db.session.commit()
    print("Migration complete: amount_paid column added, past transactions marked fully paid.")
