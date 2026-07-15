import io
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from models import db, Transaction, Customer, Item
from auth import login_required, current_user_id
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
 
reports_bp = Blueprint("reports_bp", __name__, url_prefix="/api/reports")
 
 
def build_filtered_query(args, uid):
    query = Transaction.query.filter_by(user_id=uid)
 
    start = args.get("start")
    end = args.get("end")
    customer_id = args.get("customer_id")
    item_id = args.get("item_id")
 
    if start:
        query = query.filter(Transaction.date >= datetime.strptime(start, "%Y-%m-%d"))
    if end:
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        query = query.filter(Transaction.date <= end_dt.replace(hour=23, minute=59, second=59))
    if customer_id:
        query = query.filter(Transaction.customer_id == int(customer_id))
    if item_id:
        query = query.filter(Transaction.item_id == int(item_id))
 
    sort = args.get("sort", "date_desc")
    sort_map = {
        "date_desc": Transaction.date.desc(),
        "date_asc": Transaction.date.asc(),
        "amount_desc": (Transaction.sale_price_at_time * Transaction.qty).desc(),
        "amount_asc": (Transaction.sale_price_at_time * Transaction.qty).asc(),
    }
    query = query.order_by(sort_map.get(sort, Transaction.date.desc()))
 
    return query
 
 
@reports_bp.route("/transactions", methods=["GET"])
@login_required
def filtered_transactions():
    query = build_filtered_query(request.args, current_user_id())
    txns = query.all()
 
    result = []
    total_revenue = 0
    total_profit = 0
    total_pending = 0
 
    for t in txns:
        total = t.sale_price_at_time * t.qty
        profit = (t.sale_price_at_time - t.cost_price_at_time) * t.qty
        pending = total - t.amount_paid
 
        total_revenue += total
        total_profit += profit
        total_pending += pending
 
        result.append({
            "id": t.id,
            "date": t.date.strftime("%Y-%m-%d %H:%M"),
            "customer": t.customer.name,
            "item": t.item.name,
            "qty": t.qty,
            "total": round(total, 2),
            "amount_paid": round(t.amount_paid, 2),
            "pending": round(pending, 2),
            "profit": round(profit, 2),
        })
 
    return jsonify({
        "transactions": result,
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "total_pending": round(total_pending, 2),
        "count": len(result),
    })
 
 
@reports_bp.route("/pdf", methods=["GET"])
@login_required
def export_pdf():
    query = build_filtered_query(request.args, current_user_id())
    txns = query.all()
 
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#16302A"))
    elements = []
 
    elements.append(Paragraph("Siddarth Traders — Sales Report", title_style))
    period = ""
    if request.args.get("start") or request.args.get("end"):
        period = f"Period: {request.args.get('start', 'start')} to {request.args.get('end', 'today')}"
    elements.append(Paragraph(period, styles["Normal"]))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 12))
 
    total_revenue = sum(t.sale_price_at_time * t.qty for t in txns)
    total_profit = sum((t.sale_price_at_time - t.cost_price_at_time) * t.qty for t in txns)
    total_pending = sum((t.sale_price_at_time * t.qty) - t.amount_paid for t in txns)
 
    summary_data = [
        ["Total Revenue", "Total Profit", "Total Pending", "Transactions"],
        [f"Rs. {total_revenue:,.2f}", f"Rs. {total_profit:,.2f}", f"Rs. {total_pending:,.2f}", str(len(txns))],
    ]
    summary_table = Table(summary_data, colWidths=[110, 110, 110, 90])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16302A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E4E0D6")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
 
    table_data = [["Date", "Customer", "Item", "Qty", "Total", "Paid", "Pending"]]
    for t in txns:
        total = t.sale_price_at_time * t.qty
        pending = total - t.amount_paid
        table_data.append([
            t.date.strftime("%Y-%m-%d"),
            t.customer.name,
            t.item.name,
            str(t.qty),
            f"{total:,.2f}",
            f"{t.amount_paid:,.2f}",
            f"{pending:,.2f}",
        ])
 
    txn_table = Table(table_data, repeatRows=1, colWidths=[60, 85, 85, 35, 60, 55, 55])
    txn_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16302A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E4E0D6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F3EC")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(txn_table)
 
    doc.build(elements)
    buffer.seek(0)
 
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"sales_report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mimetype="application/pdf",
    )