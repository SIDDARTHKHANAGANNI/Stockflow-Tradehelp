# StockFlow — Inventory, CRM & Business Intelligence Platform

A full-stack business management system built for a real lubricant distribution business (Siddarth Traders, Gokak). Replaces manual stock registers and paper invoicing with a live, multi-user web application covering inventory, customer relationships, sales, payments, analytics, and an AI-powered business assistant.

## Live Demo

- Deployed on Render / Vercel *http://stockflow-tradehelp.vercel.app/*

## Features

### Inventory & Stock
- Add, edit, delete items with cost/sale price and reorder thresholds
- Manual stock adjustments logged with full audit trail (`stock_log`)
- Automatic stock deduction on every sale
- Low-stock flagging with **automated supplier email alerts** via SMTP

### Customer Management
- Full CRM: name, phone, address, town/city, and geolocation
- Interactive map (Leaflet + OpenStreetMap) — click to pin customer location
- Filter customer list by town/city
- Per-customer detail page: purchase history, total revenue, profit, and pending balance, with a dedicated revenue/profit trend chart

### Sales & Payments
- Record sales against a customer and item, with automatic stock deduction and profit calculation
- **Partial payment tracking** — record amount paid now vs. pending, editable after the fact as payments come in
- Undo/reverse a sale (restores stock)

### Dashboards & Reporting
- Real-time dashboard: revenue, profit, stock sold, pending amounts
- Revenue & profit trend chart, top-selling items chart
- Business snapshot: customer/item counts, low-stock count, average order value, top customer, top item
- Dedicated Reports page: date-range filtering, sort by date/amount, filter by customer/item, **PDF export** of any filtered report (via ReportLab)

### AI Business Assistant
- Floating chat widget available on every page
- Natural-language Q&A grounded in **live business data** (revenue, pending payments, low stock, top customers/items, recent transactions) via an LLM API (OpenRouter/Claude)
- Retrieval-style grounding — the model answers only from real data pulled from the database at query time, not from memory

### Authentication & Multi-Tenancy
- Secure signup/login (hashed passwords via Werkzeug)
- Persistent sessions (30-day, no unexpected logout)
- Fully isolated per-user data — every customer, item, and transaction is scoped to its owner
- Profile page: edit details, change password, delete account (with full data cleanup)

### Deployment & DevOps
- Dockerized for consistent, portable deployment across environments
- Dual deployment support: traditional (Render, Gunicorn) and serverless (Vercel)
- Environment-based configuration, serverless-safe DB connection pooling (Neon pooled endpoint)

### Design & UX
- Custom design system — no default browser dialogs; all confirms/prompts use a styled modal matching the app's theme
- Fully responsive — mobile hamburger nav, stacking layouts, touch-friendly map and forms

## Tech Stack

**Backend:** Python, Flask, Flask-SQLAlchemy, Gunicorn
**Database:** PostgreSQL (Neon, serverless)
**Frontend:** Vanilla JS, HTML5, CSS3 (custom design system, no framework)
**Charts:** Chart.js
**Maps:** Leaflet.js + OpenStreetMap
**PDF Generation:** ReportLab
**AI:** OpenRouter API (Claude)
**DevOps:** Docker, Gunicorn
**Deployment:** Render / Vercel (serverless-compatible)

## Architecture

```
Stockflow/
├── app.py                   # Flask app factory, routes, session config
├── config.py                 # Environment-based configuration
├── models.py                  # SQLAlchemy models (User, Customer, Item, Transaction, StockLog)
├── auth.py                    # Login-required decorator, session helpers
├── routes_auth.py             # Signup, login, logout, profile, account deletion
├── routes_customer.py         # Customer CRUD
├── routes_item.py             # Item/stock CRUD
├── routes_transaction.py      # Sales, payments, customer purchase history
├── routes_analytics.py        # Dashboard summary, snapshot, monthly trends
├── routes_reports.py          # Filtered reports + PDF export
├── routes_email.py            # Low-stock SMTP alerts
├── routes_assistant.py        # AI business assistant (RAG-style grounding)
├── static/
│   ├── style.css               # Design system (custom, responsive)
│   └── modal.js                 # Custom modal system (confirm/prompt replacement)
├── templates/                 # Jinja2 templates (dashboard, customers, items, sales, reports, etc.)
├── api/index.py                # Vercel serverless entry point
└── vercel.json                  # Vercel routing/build config
```

## Setup

### 1. Clone and install
```bash
git clone <repo-url>
cd Stockflow
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
Copy `.env.example` to `.env` and fill in:
```
DATABASE_URL=postgresql+psycopg://user:pass@host/db?sslmode=require
SECRET_KEY=your-random-secret
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-gmail-app-password
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

### 3. Initialize database
```bash
python init_db.py
```

### 4. Run
```bash
python app.py
```
Visit `http://localhost:5000`

## Deployment

Supports both traditional (Render, Gunicorn) and serverless (Vercel) deployment out of the box. See `vercel.json` for serverless configuration — uses Neon's pooled connection string for serverless-safe database access.

### Docker
```bash
docker build -t stockflow .
docker run -p 5000:5000 --env-file .env stockflow
```

## Author

**Siddarth Khanaganni**
B.Tech (Hons) Computer Science & Engineering, RV University, Bengaluru