# ☕ Smart Cafe — Cloud-Based QR Ordering & Management System

<div align="center">

![Smart Cafe Banner](https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=1200&h=400&fit=crop&q=80)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-smart--cafe--app.netlify.app-brightgreen?style=for-the-badge&logo=netlify)](https://smart-cafe-app.netlify.app)
[![API Docs](https://img.shields.io/badge/API%20Docs-onrender.com%2Fdocs-blue?style=for-the-badge&logo=fastapi)](https://smart-cafe-api.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.11-yellow?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-green?style=for-the-badge&logo=supabase)](https://supabase.com)

**A full-stack, AI-powered cafe ordering and management system. Customers scan a QR code at their table, browse the live menu, and place orders — kitchen staff see them instantly. Admins get real-time analytics, forecasting, and full operations control.**

</div>

---

## 📋 Table of Contents

- [Live Demo](#-live-demo)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [AI / ML Engine](#-ai--ml-engine)
- [Database Schema](#-database-schema)
- [Local Setup](#-local-setup)
- [Cloud Deployment](#-cloud-deployment)
- [Environment Variables](#-environment-variables)
- [Screenshots](#-screenshots)
- [Developer](#-developer)

---

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | https://smart-cafe-app.netlify.app |
| **Backend API** | https://smart-cafe-api.onrender.com |
| **API Docs (Swagger)** | https://smart-cafe-api.onrender.com/docs |
| **Admin Login** | https://smart-cafe-app.netlify.app/admin-login.html |

> **Note:** Backend runs on Render free tier — first request after inactivity takes ~30 seconds to wake up.

---

## ✨ Features

### 👥 Customer Experience
- **QR Code Ordering** — Scan table QR → browse live menu → add to cart → place order. No app download needed.
- **Live Order Tracking** — Real-time order status updates (Placed → Preparing → Ready → Served) via Supabase Realtime
- **AI Recommendations** — Personalised "You may also like" suggestions based on order history and collaborative filtering
- **Table Reservation** — Book a table online with conflict detection and capacity validation
- **Digital Cart** — Persistent cart with quantity controls, subtotal, 9% service tax calculation

### 👨‍🍳 Kitchen Operations
- **Live Kanban Board** — Active / Preparing / Ready tabs with real-time order cards
- **Overtime Detection** — Orders older than 15 minutes flagged as URGENT with red highlight
- **One-Click Status Updates** — Start Preparing → Mark Ready → Mark Served
- **Auto Table Release** — Table marked available automatically when order served

### 🛠️ Admin Dashboard
- **Revenue Analytics** — Daily/weekly/monthly sales charts with Chart.js
- **Peak Hours Analysis** — Orders by hour heatmap for staffing decisions
- **Popular Items** — Top 10 most ordered items with revenue breakdown
- **Menu Management** — Full CRUD, image upload via Cloudinary, availability toggle
- **Table Board (Cafe Vista)** — Live floor plan with zone filtering, Quick Seat, Clean Up, Flow analysis
- **Reservation Management** — View, confirm, cancel bookings with conflict detection
- **Transaction Ledger (Fin Ledger)** — Payment records with CSV export, method filtering, slide-in detail panel
- **Email Templates (NotifyPro)** — 4 HTML email templates, send test emails, notification log
- **QR Generator** — Auto-generates QR codes for all tables, downloads as print-ready PNG

### 🤖 AI / ML Features
- **Collaborative Filtering** — Item-item co-occurrence matrix for "others also ordered" recommendations
- **Content-Based Filtering** — Tag and category similarity matching
- **Demand Forecasting** — 7-day order volume and revenue forecast using Exponential Smoothing + day-of-week seasonality
- **Sentiment Analysis** — Lexicon-based review sentiment scoring (positive/neutral/negative) with negation and intensifier handling
- **Menu Intelligence** — Star/Plow-Horse/Dog item classification for menu optimisation
- **AI Staffing Recommendations** — Shift recommendations based on historical peak hour analysis

### 📧 Notifications
- **Order Ready Email** — HTML email with order items, table number, total
- **Reservation Confirmed** — Styled confirmation with date, time, guest count
- **Reservation Reminder** — Day-of reminder with booking details
- **Order Preparing** — Kitchen started notification with progress bar
- Sent via Gmail SMTP, logged to database

### 🎯 Loyalty System
- Points earned on every served order (10% of order value)
- Redemption endpoint
- Per-customer balance tracking

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.11** | Runtime |
| **FastAPI** | REST API framework — async, auto Swagger docs |
| **Supabase Python SDK** | Database client |
| **Pydantic v2** | Request/response validation and serialisation |
| **python-dotenv** | Environment variable management |
| **httpx** | Async HTTP client for Cloudinary uploads |
| **smtplib** | Email sending via Gmail SMTP |
| **uvicorn** | ASGI server |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Vanilla JavaScript (ES2022)** | No framework — pure JS |
| **Tailwind CSS (CDN)** | Utility-first styling |
| **Work Sans (Google Fonts)** | Typography |
| **Material Symbols Outlined** | Icons |
| **Chart.js** | Revenue and analytics charts |
| **Supabase JS SDK** | Realtime subscriptions |
| **QuickChart.io API** | QR code generation |

### Database & Cloud
| Service | Role |
|---------|------|
| **Supabase (PostgreSQL)** | Primary database + Realtime pub/sub |
| **Supabase Row Level Security** | Per-table access control |
| **Cloudinary** | Menu item image storage and CDN delivery |
| **Render** | Backend (FastAPI) hosting |
| **Netlify** | Frontend static site hosting |
| **Gmail SMTP** | Transactional email delivery |
| **GitHub** | Version control + CI/CD trigger |

### AI / ML (Pure Python — no heavy frameworks)
| Module | Algorithm |
|--------|-----------|
| `ml/recommendations.py` | Item-item co-occurrence matrix, cosine similarity, content-based tag matching, popularity fallback |
| `ml/forecasting.py` | Simple Exponential Smoothing (α=0.35), day-of-week seasonality factors, confidence intervals |
| `ml/sentiment.py` | Lexicon-based scoring with negation window, intensifier/diminisher weighting |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CUSTOMER / STAFF                     │
│              (Any browser, any device)                  │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────────────┐
│              NETLIFY (Frontend)                         │
│   13 HTML pages + Vanilla JS + Tailwind CSS             │
│   config.js → points all fetch() to Render API         │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API calls (HTTPS + CORS)
┌─────────────────────▼───────────────────────────────────┐
│              RENDER (Backend)                           │
│   FastAPI (Python 3.11) — uvicorn                      │
│   10 Routers: menu, orders, tables, reservations,      │
│   analytics, ai, reviews, customers,                   │
│   notifications, settings                              │
│   3 ML modules: recommendations, forecasting,          │
│   sentiment                                             │
└──────────┬──────────────────────────┬───────────────────┘
           │ Supabase SDK             │ httpx (image upload)
┌──────────▼──────────┐   ┌──────────▼───────────────────┐
│ SUPABASE            │   │ CLOUDINARY                   │
│ PostgreSQL + RLS    │   │ Menu image storage + CDN     │
│ Realtime pub/sub    │   └──────────────────────────────┘
│ 10 tables           │
│ Triggers + Functions│
└─────────────────────┘
           │ Realtime WebSocket
┌──────────▼──────────────────────────────────────────────┐
│  Browser Supabase JS SDK (Realtime Subscriptions)       │
│  kitchen.html / order-status.html / admin-tables.html   │
│  Live updates without page refresh                      │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
smart-cafe/
│
├── backend/
│   ├── main.py                  # FastAPI app — all routers mounted, CORS, health check
│   ├── config.py                # Settings class — reads from .env via python-dotenv
│   ├── database.py              # Supabase client singleton
│   ├── auth.py                  # verify_admin() dependency — x-admin-token header
│   ├── models.py                # All Pydantic request/response models
│   ├── requirements.txt         # Pinned Python dependencies
│   ├── .env.example             # Template — copy to .env and fill in
│   │
│   ├── routers/
│   │   ├── menu.py              # GET/POST/PUT/DELETE menu items + Cloudinary upload
│   │   ├── orders.py            # Place order, kitchen view, status lifecycle, table auto-management
│   │   ├── tables.py            # Table status, zone grouping, QR URL generation
│   │   ├── reservations.py      # Conflict detection, capacity check, availability query
│   │   ├── analytics.py         # Daily/weekly/monthly sales, peak hours, popular items, staffing
│   │   ├── ai.py                # Recommendations, forecasting, sentiment, menu insights
│   │   ├── reviews.py           # Submit + auto-sentiment, admin moderation
│   │   ├── customers.py         # Profiles, loyalty points, redeem
│   │   ├── notifications.py     # 4 HTML email templates, SMTP send, notification log
│   │   └── settings.py          # Cafe-wide config key-value, Cloudinary sign endpoint
│   │
│   └── ml/
│       ├── recommendations.py   # Collaborative + content-based + popularity fallback
│       ├── forecasting.py       # Exponential smoothing + seasonality demand forecast
│       └── sentiment.py         # Lexicon-based sentiment with negation/intensifiers
│
├── frontend/
│   ├── index.html               # Landing page + reservation form
│   ├── menu.html                # QR table menu + cart + place order
│   ├── order-status.html        # Live order tracking (Supabase Realtime)
│   ├── admin-login.html         # Role-based login: Customer / Kitchen / Admin
│   ├── admin-dashboard.html     # KPIs + revenue chart + peak hours + popular items
│   ├── admin-menu.html          # Menu CRUD + Cloudinary image upload + availability toggle
│   ├── admin-tables.html        # Live floor plan + Quick Seat + Clean Up + Flow modals
│   ├── admin-reservations.html  # Reservation list + confirm/cancel
│   ├── admin-analytics.html     # Predictive analytics + 7-day demand forecast
│   ├── admin-transactions.html  # Payment ledger (Fin Ledger) + CSV export
│   ├── admin-notifications.html # Email template manager (NotifyPro) + send test
│   ├── kitchen.html             # Kitchen kanban board (Realtime)
│   ├── qr-generator.html        # Auto-generate + print QR codes for all tables
│   ├── js/
│   │   └── config.js            # API URL, Supabase keys, admin token — UPDATE THIS
│   └── css/
│       └── style.css            # Shared: toasts, spinner, badges, scrollbar
│
└── schema.sql                   # Complete Supabase DB schema — run once in SQL Editor
```

---

## 🔌 API Reference

All endpoints served at `https://smart-cafe-api.onrender.com`

Admin endpoints require header: `x-admin-token: <your_token>`

```
MENU ──────────────────────────────────────────────────
GET    /menu                     Available items (filter: ?category=Coffee)
GET    /menu/all                 Admin: all items including unavailable
GET    /menu/categories          Distinct category list
GET    /menu/search?q=latte      Search by name / description / tag
GET    /menu/{id}                Single item
POST   /menu                     Admin: create
PUT    /menu/{id}                Admin: update
PATCH  /menu/{id}/toggle         Admin: toggle availability
DELETE /menu/{id}                Admin: delete
POST   /menu/{id}/upload-image   Admin: upload to Cloudinary

ORDERS ────────────────────────────────────────────────
POST   /orders                   Place order (customer-facing)
GET    /orders                   Admin: all orders
GET    /orders/kitchen           Kitchen: placed + preparing + ready
GET    /orders/{id}              Single order with items
PUT    /orders/{id}/status       Update: placed→preparing→ready→served→cancelled

TABLES ────────────────────────────────────────────────
GET    /tables                   All tables with live status + active order
GET    /tables/zones             Tables grouped by zone
PUT    /tables/{id}              Update status

RESERVATIONS ──────────────────────────────────────────
POST   /reservations             Create (conflict + capacity check)
GET    /reservations             Admin: list (filter: ?res_date=YYYY-MM-DD)
GET    /reservations/availability Check free tables for date/time/guests
PUT    /reservations/{id}        Update status

ANALYTICS ─────────────────────────────────────────────
GET    /analytics/daily-sales         Today's revenue summary
GET    /analytics/weekly-sales        Past 7 days by day
GET    /analytics/peak-hours          Orders by hour
GET    /analytics/popular-items       Top 10 items
GET    /analytics/revenue-by-category Revenue % per category
GET    /analytics/staffing-recommendations AI shift recommendations
GET    /analytics/summary             Full dashboard summary (single call)

AI / ML ───────────────────────────────────────────────
GET    /ai/recommendations?table_id=  Personalised menu recs
GET    /ai/forecast/orders?days=7     Order volume forecast
GET    /ai/forecast/revenue?days=7    Revenue forecast
GET    /ai/forecast/peak-hours        Peak hour predictions
POST   /ai/reviews                    Submit review + auto-sentiment
GET    /ai/reviews/summary            Sentiment analytics
GET    /ai/menu-insights              Star/Dog/Plow-Horse analysis

NOTIFICATIONS ─────────────────────────────────────────
POST   /notifications/send       Send notification email
POST   /notifications/test       Send test email
GET    /notifications/log        Sent email log

HEALTH ────────────────────────────────────────────────
GET    /                         API status
GET    /health                   Database connectivity check
GET    /docs                     Interactive Swagger UI
```

---

## 🤖 AI / ML Engine

### 1. Recommendation System (`ml/recommendations.py`)

Three-tier strategy — automatically selects best approach per customer:

```
Customer has 2+ orders → Collaborative Filtering
  → Item-item co-occurrence matrix from all order history
  → Cosine similarity between items
  → Recommend what co-occurs most with ordered items

Customer has 1 order → Content-Based Filtering
  → Build preference profile from ordered item tags/categories
  → Score all menu items by tag overlap
  → Recommend highest-scoring unseen items

New customer (no history) → Popularity Fallback
  → Rank by total order count across all customers
  → Boost featured items
  → Return top N
```

### 2. Demand Forecasting (`ml/forecasting.py`)

```
1. Load last 30 days of daily order counts from DB
2. Apply Simple Exponential Smoothing (α = 0.35)
3. Calculate linear trend from last 3 data points
4. Compute day-of-week seasonality factors
   (e.g. weekends 1.4x, Mondays 0.7x of average)
5. Project: base = smoothed[-1] + slope × day
   seasonal = base × dow_factor
6. Confidence interval: ± 1.5 × std_dev of residuals
7. Return 7-day forecast with projected_orders,
   confidence_low, confidence_high per day
```

### 3. Sentiment Analysis (`ml/sentiment.py`)

```
Input: "Not very good, quite slow service"
Process:
  - Tokenise → ["not","very","good","quite","slow","service"]
  - "good" = +1.0, "very" before it = intensifier (+1.5 raw)
  - "not" in 3-word lookback → negate → -1.5
  - "slow" = -1.0, "quite" = diminisher → -0.5
  - Raw score: -1.5 - 0.5 = -2.0
  - Normalise to [0,1]: (-2 + 5) / 10 = 0.30
Output: { sentiment: "negative", score: 0.30 }
```

---

## 🗄 Database Schema

10 tables in Supabase PostgreSQL:

| Table | Purpose |
|-------|---------|
| `tables` | Physical cafe tables with status and zone |
| `menu_items` | Menu with category, tags, allergens, image URL |
| `orders` | Orders with status lifecycle and payment |
| `order_items` | Line items linking orders to menu items |
| `reservations` | Table bookings with conflict prevention |
| `customers` | Customer profiles and visit history |
| `reviews` | Star ratings with sentiment score |
| `loyalty_points` | Earned/redeemed points log |
| `notifications` | Sent email log |
| `cafe_settings` | Key-value store for cafe config |

**Key database features:**
- Row Level Security (RLS) on all tables
- `update_updated_at_column()` trigger — auto-timestamps
- `set_served_at()` trigger — records when order served
- `award_loyalty_points()` trigger — auto-awards points on serve
- Indexes on `orders.status`, `orders.created_at`, `reservations.reservation_date`
- Supabase Realtime enabled on `orders`, `tables`, `order_items`, `reservations`

---

## 💻 Local Setup

### Prerequisites
- Python 3.11+
- VS Code + Live Server extension
- Supabase account (free)
- Cloudinary account (free)

### 1. Clone the repo
```bash
git clone https://github.com/Vaidik-7781/smart-cafe.git
cd smart-cafe
```

### 2. Set up Supabase
1. Create project at https://supabase.com
2. SQL Editor → paste entire `schema.sql` → Run
3. Enable Realtime (run each separately):
```sql
alter publication supabase_realtime add table orders;
alter publication supabase_realtime add table tables;
alter publication supabase_realtime add table order_items;
alter publication supabase_realtime add table reservations;
```
4. Settings → API → copy Project URL, anon key, service_role key

### 3. Backend setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your real values
uvicorn main:app --reload --port 8000
```

Verify: http://localhost:8000/health → `{"status":"healthy","database":"ok"}`

### 4. Frontend setup
1. Open `frontend/js/config.js`
2. Set `API_URL: "http://localhost:8000"`
3. Fill in `SUPABASE_URL` and `SUPABASE_ANON_KEY`
4. Set `ADMIN_TOKEN` to match your `.env`
5. Right-click `frontend/index.html` → Open with Live Server

App runs at http://127.0.0.1:5500/frontend/index.html

---

## ☁️ Cloud Deployment

### Backend → Render

1. Push repo to GitHub
2. render.com → New → Web Service → Connect repo
3. Settings:

| Field | Value |
|-------|-------|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Environment | Add all vars from `.env` |

4. Deploy → get URL: `https://smart-cafe-api.onrender.com`

### Frontend → Netlify

1. Update `frontend/js/config.js` → `API_URL: "https://smart-cafe-api.onrender.com"`
2. netlify.com → Add new site → Deploy manually
3. Drag `frontend/` folder → deployed in 30 seconds
4. Update `FRONTEND_URL` in Render environment vars

### Auto-redeploy workflow
```bash
git add .
git commit -m "your change"
git push
# Render auto-redeploys backend
# Drag frontend/ to Netlify for frontend updates
```

---

## 🔐 Environment Variables

Create `backend/.env` (never commit this file):

```env
# Supabase (get from: supabase.com → Settings → API)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key          # service_role (not anon)

# Admin auth (must match ADMIN_TOKEN in config.js)
ADMIN_TOKEN=your-strong-secret-token

# Gmail SMTP (get App Password from myaccount.google.com)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=your-16-char-app-password
FROM_EMAIL=noreply@smartcafe.in
FROM_NAME=Smart Cafe

# Cloudinary (get from cloudinary.com → Dashboard)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
CLOUDINARY_UPLOAD_PRESET=cafe_menu_images

# App
ENVIRONMENT=development
FRONTEND_URL=http://127.0.0.1:5500
TAX_RATE=0.09
JWT_SECRET=your-jwt-secret
```

---

## 📊 Pages Overview

| Page | Route | Who uses it |
|------|-------|-------------|
| Landing Page | `/index.html` | Everyone |
| QR Menu | `/menu.html?table=N&table_id=UUID` | Customers |
| Order Tracking | `/order-status.html?order_id=UUID` | Customers |
| Login | `/admin-login.html` | Staff + Admin |
| Kitchen Board | `/kitchen.html` | Kitchen staff |
| Admin Dashboard | `/admin-dashboard.html` | Admin |
| Menu Manager | `/admin-menu.html` | Admin |
| Table Board | `/admin-tables.html` | Admin + Floor staff |
| Reservations | `/admin-reservations.html` | Admin |
| Analytics | `/admin-analytics.html` | Admin |
| Transactions | `/admin-transactions.html` | Admin |
| Notifications | `/admin-notifications.html` | Admin |
| QR Generator | `/qr-generator.html` | Admin |

---

## 🆓 Cloud Services Cost

| Service | Free Tier | Paid if needed |
|---------|-----------|----------------|
| Supabase | 500MB DB, unlimited requests | $25/mo (Pro) |
| Render | 750 hrs/mo, sleeps after 15 min | $7/mo (always-on) |
| Netlify | Unlimited bandwidth | $19/mo (Pro) |
| Cloudinary | 25GB storage, 25GB bandwidth | $89/mo (Plus) |
| Gmail SMTP | 500 emails/day | Google Workspace $6/mo |

**Total for small cafe: $0/month** (free tiers sufficient for <500 orders/day)

---

## 🔒 Security Notes

- `service_role` key lives **only** in backend `.env` — never in frontend
- Frontend uses `anon` key (limited read-only via RLS)
- Admin token verified on every protected endpoint via `x-admin-token` header
- `.env` in `.gitignore` — never committed
- RLS policies on all Supabase tables
- CORS restricted to `FRONTEND_URL` in production

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 👨‍💻 Developer

<div align="center">

**Vaidik Gupta**

[![GitHub](https://img.shields.io/badge/GitHub-Vaidik--7781-black?style=for-the-badge&logo=github)](https://github.com/Vaidik-7781)

*Built with FastAPI, Supabase, Vanilla JS, and a lot of ☕*

</div>
