"""
One-time migration for the new auth system.
1. Creates the `users` table (if missing).
2. Adds user_id columns to customers, items, transactions (if missing).
3. Creates a default account for your existing test data (so nothing is lost),
   and assigns all existing rows to it.

Usage: python migrate_add_auth.py
"""
from app import create_app
from models import db, User
from sqlalchemy import text

DEFAULT_USERNAME = "siddarth"
DEFAULT_PASSWORD = "changeme123"  # change this after logging in via Profile page

app = create_app()

with app.app_context():
    # 1. create any missing tables (this creates `users` since it's new)
    db.create_all()

    # 2. add user_id columns to existing tables if not already present
    db.session.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS user_id INTEGER"))
    db.session.execute(text("ALTER TABLE items ADD COLUMN IF NOT EXISTS user_id INTEGER"))
    db.session.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS user_id INTEGER"))
    db.session.commit()

    # 3. create a default legacy user if one doesn't exist, assign old data to them
    legacy_user = User.query.filter_by(username=DEFAULT_USERNAME).first()
    if not legacy_user:
        legacy_user = User(username=DEFAULT_USERNAME, name="Siddarth")
        legacy_user.set_password(DEFAULT_PASSWORD)
        db.session.add(legacy_user)
        db.session.commit()
        print(f"Created default account -> username: {DEFAULT_USERNAME}, password: {DEFAULT_PASSWORD}")
    else:
        print(f"Default account already exists -> username: {DEFAULT_USERNAME}")

    db.session.execute(text(f"UPDATE customers SET user_id = {legacy_user.id} WHERE user_id IS NULL"))
    db.session.execute(text(f"UPDATE items SET user_id = {legacy_user.id} WHERE user_id IS NULL"))
    db.session.execute(text(f"UPDATE transactions SET user_id = {legacy_user.id} WHERE user_id IS NULL"))
    db.session.commit()

    # 4. now enforce NOT NULL since all rows have a value
    db.session.execute(text("ALTER TABLE customers ALTER COLUMN user_id SET NOT NULL"))
    db.session.execute(text("ALTER TABLE items ALTER COLUMN user_id SET NOT NULL"))
    db.session.execute(text("ALTER TABLE transactions ALTER COLUMN user_id SET NOT NULL"))
    db.session.commit()

    print("Migration complete. Log in with the credentials above, then change your password in Profile.")
