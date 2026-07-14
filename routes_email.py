import smtplib
from email.mime.text import MIMEText
from flask import Blueprint, jsonify, current_app
from models import Item

email_bp = Blueprint("email_bp", __name__, url_prefix="/api/email")


def send_email(to_email, subject, body):
    smtp_user = current_app.config["SMTP_USER"]
    smtp_pass = current_app.config["SMTP_PASS"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())


@email_bp.route("/low-stock-alert", methods=["POST"])
def low_stock_alert():
    low_items = Item.query.filter(Item.current_stock <= Item.reorder_threshold).all()

    if not low_items:
        return jsonify({"message": "no low-stock items, nothing sent"}), 200

    sent = []
    skipped = []

    for item in low_items:
        if not item.supplier_email:
            skipped.append(item.name)
            continue

        subject = f"Stock Order Request - {item.name}"
        body = (
            f"Hello,\n\n"
            f"Stock for {item.name} is running low.\n"
            f"Current stock: {item.current_stock}\n"
            f"Reorder threshold: {item.reorder_threshold}\n\n"
            f"Please arrange for restock at your earliest convenience.\n\n"
            f"Regards,\nSiddarth Traders"
        )

        try:
            send_email(item.supplier_email, subject, body)
            sent.append(item.name)
        except Exception as e:
            skipped.append(f"{item.name} (error: {str(e)})")

    return jsonify({"sent": sent, "skipped": skipped})
