import requests
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func
from models import db, Transaction, Customer, Item
from auth import login_required, current_user_id

assistant_bp = Blueprint("assistant_bp", __name__, url_prefix="/api/assistant")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "tencent/hy3:free"


def gather_business_context(uid):
    """Pull a compact, current snapshot of the business for grounding the model's answer."""
    txns = Transaction.query.filter_by(user_id=uid).all()
    total_revenue = sum(t.sale_price_at_time * t.qty for t in txns)
    total_profit = sum((t.sale_price_at_time - t.cost_price_at_time) * t.qty for t in txns)
    total_pending = sum((t.sale_price_at_time * t.qty) - t.amount_paid for t in txns)

    low_stock = (
        Item.query.filter(Item.user_id == uid, Item.current_stock <= Item.reorder_threshold)
        .all()
    )

    pending_by_customer = (
        db.session.query(
            Customer.name,
            func.sum(Transaction.sale_price_at_time * Transaction.qty - Transaction.amount_paid).label("pending"),
        )
        .join(Transaction, Transaction.customer_id == Customer.id)
        .filter(Customer.user_id == uid, Transaction.user_id == uid)
        .group_by(Customer.name)
        .having(func.sum(Transaction.sale_price_at_time * Transaction.qty - Transaction.amount_paid) > 0)
        .order_by(func.sum(Transaction.sale_price_at_time * Transaction.qty - Transaction.amount_paid).desc())
        .limit(10)
        .all()
    )

    top_items = (
        db.session.query(Item.name, func.sum(Transaction.qty).label("qty"))
        .join(Transaction, Transaction.item_id == Item.id)
        .filter(Item.user_id == uid, Transaction.user_id == uid)
        .group_by(Item.name)
        .order_by(func.sum(Transaction.qty).desc())
        .limit(10)
        .all()
    )

    recent_txns = (
        Transaction.query.filter_by(user_id=uid).order_by(Transaction.date.desc()).limit(15).all()
    )

    lines = []
    lines.append(f"TOTAL REVENUE (all time): Rs. {total_revenue:,.2f}")
    lines.append(f"TOTAL PROFIT (all time): Rs. {total_profit:,.2f}")
    lines.append(f"TOTAL PENDING PAYMENTS (all time): Rs. {total_pending:,.2f}")
    lines.append(f"TOTAL CUSTOMERS: {Customer.query.filter_by(user_id=uid).count()}")
    lines.append(f"TOTAL ITEMS: {Item.query.filter_by(user_id=uid).count()}")
    lines.append(f"TOTAL TRANSACTIONS: {len(txns)}")

    lines.append("\nLOW STOCK ITEMS (at or below reorder threshold):")
    if low_stock:
        for i in low_stock:
            lines.append(f"- {i.name}: {i.current_stock} units left (threshold {i.reorder_threshold})")
    else:
        lines.append("- none currently")

    lines.append("\nCUSTOMERS WITH PENDING PAYMENTS (highest first):")
    if pending_by_customer:
        for name, pending in pending_by_customer:
            lines.append(f"- {name}: Rs. {pending:,.2f} pending")
    else:
        lines.append("- none, all customers fully paid")

    lines.append("\nTOP SELLING ITEMS BY QUANTITY:")
    for name, qty in top_items:
        lines.append(f"- {name}: {qty} units sold")

    lines.append("\nMOST RECENT TRANSACTIONS:")
    for t in recent_txns:
        total = t.sale_price_at_time * t.qty
        lines.append(
            f"- {t.date.strftime('%Y-%m-%d')}: {t.customer.name} bought {t.qty}x {t.item.name} "
            f"for Rs. {total:,.2f} (paid Rs. {t.amount_paid:,.2f})"
        )

    return "\n".join(lines)


@assistant_bp.route("/ask", methods=["POST"])
@login_required
def ask():
    api_key = current_app.config.get("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"error": "AI assistant not configured. Add OPENROUTER_API_KEY to your .env file."}), 503

    data = request.get_json()
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question required"}), 400

    context = gather_business_context(current_user_id())

    system_prompt = (
        "You are a business assistant for a small lubricant distribution business (Siddarth Traders). "
        "Answer the owner's question using ONLY the business data provided below. "
        "Be concise and direct — 2-4 sentences unless a list is clearly needed. "
        "Use Rs. for currency. If the data doesn't contain the answer, say so plainly rather than guessing.\n\n"
        "=== CURRENT BUSINESS DATA ===\n" + context
    )

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 400,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
            },
            timeout=20,
        )
        resp.raise_for_status()
        result = resp.json()
        answer = result["choices"][0]["message"]["content"]
        return jsonify({"answer": answer})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"AI request failed: {str(e)}"}), 502
