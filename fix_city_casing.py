"""
One-time cleanup: normalizes existing city values so "gokak", "GOKAK",
"Gokak " etc. all become "Gokak" — fixes duplicates already in the DB.
Usage: python fix_city_casing.py
"""
from app import create_app
from models import db, Customer

app = create_app()

with app.app_context():
    customers = Customer.query.filter(Customer.city.isnot(None)).all()
    count = 0
    for c in customers:
        normalized = c.city.strip().title()
        if c.city != normalized:
            c.city = normalized
            count += 1
    db.session.commit()
    print(f"Normalized {count} customer city values.")
