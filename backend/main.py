"""
main.py — Smart Cafe FastAPI Application
════════════════════════════════════════════════════════════════
Run locally:   uvicorn main:app --reload --port 8000
Production:    uvicorn main:app --host 0.0.0.0 --port 10000
Docs:          http://localhost:8000/docs
════════════════════════════════════════════════════════════════
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from config import settings

# ── Import all routers ────────────────────────────────────────────────────────
from routers import menu, orders, tables, reservations, analytics, ai, reviews, customers, notifications, settings as settings_router


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" Smart Cafe API starting up…")
    print(f" Environment : {settings.ENVIRONMENT}")
    print(f" Supabase    : {settings.SUPABASE_URL[:40]}..." if settings.SUPABASE_URL else " Supabase    : NOT CONFIGURED")
    print(f" SMTP Email  : {'✅ ' + settings.SMTP_USER if settings.SMTP_USER else '⚠️  Not configured (emails skipped)'}")
    print(f" Cloudinary  : {'✅ ' + settings.CLOUDINARY_CLOUD_NAME if settings.CLOUDINARY_CLOUD_NAME else '⚠️  Not configured (images skipped)'}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    yield
    print("Smart Cafe API shutting down…")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Cafe API",
    description="""
## 🍵 Smart Cafe – Complete REST API

### Features
- **Menu** – CRUD, image upload, categories, search
- **Orders** – Place, track, kitchen view, status lifecycle
- **Tables** – Real-time status, zone management, QR URLs
- **Reservations** – Conflict detection, availability check, time slots
- **Analytics** – Daily/weekly sales, peak hours, revenue by category
- **AI / ML** – Personalised recommendations, demand forecasting, sentiment analysis
- **Reviews** – Submit with auto-sentiment scoring, admin moderation
- **Customers** – Profiles, loyalty points, visit history
- **Notifications** – Email templates (SMTP), send test, log
- **Settings** – Cafe-wide config, Cloudinary signed upload

### Authentication
Admin-only endpoints require header:  `x-admin-token: <your_token>`
""",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{(time.time() - start)*1000:.1f}ms"
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(tables.router)
app.include_router(reservations.router)
app.include_router(analytics.router)
app.include_router(ai.router)
app.include_router(reviews.router)
app.include_router(customers.router)
app.include_router(notifications.router)
app.include_router(settings_router.router)


# ── Root & Health ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "message":     "Smart Cafe API is running 🍵",
        "version":     "2.0.0",
        "environment": settings.ENVIRONMENT,
        "docs":        "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    """Lightweight health check for deployment platforms (Render, Railway, etc.)"""
    from database import supabase
    try:
        supabase.table("cafe_settings").select("key").limit(1).execute()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)[:60]}"

    return JSONResponse({
        "status":      "healthy" if db_status == "ok" else "degraded",
        "database":    db_status,
        "environment": settings.ENVIRONMENT,
    }, status_code=200 if db_status == "ok" else 503)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"[UNHANDLED ERROR] {request.url} → {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url)}
    )