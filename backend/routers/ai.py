"""
routers/ai.py — AI/ML API endpoints.
  GET  /ai/recommendations          — per-table personalised recs
  GET  /ai/forecast/orders          — 7-day order volume forecast
  GET  /ai/forecast/revenue         — 7-day revenue forecast
  POST /ai/reviews/analyse          — analyse a new review
  GET  /ai/reviews/summary          — sentiment overview of all reviews
  GET  /ai/menu-insights            — AI-powered menu optimisation tips
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import date, timedelta
from collections import defaultdict

from database import supabase
from auth import verify_admin
from models import ReviewCreate
from ml.recommendations import get_recommendations
from ml.forecasting import forecast_next_n_days, forecast_revenue, peak_hour_forecast
from ml.sentiment import analyse_sentiment, batch_analyse

router = APIRouter(prefix="/ai", tags=["AI / ML"])


# ── Recommendations ──────────────────────────────────────────────────────────

@router.get("/recommendations", summary="Get personalised menu recommendations")
def recommendations(
    table_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    top_n: int = 5
):
    """
    Return personalised recommendations for a customer.
    Looks up their order history from today/current session.
    Falls back to popularity if no history.
    """
    # Load all available menu items
    all_items = supabase.table("menu_items").select("*")\
        .eq("is_available", True).execute().data

    # Load all order items for co-occurrence
    all_order_items = supabase.table("order_items")\
        .select("order_id, menu_item_id, quantity").execute().data

    # Customer history: orders from this table (today) or by name
    history = []
    if table_id:
        history_res = supabase.table("orders")\
            .select("id, order_items(menu_item_id, menu_items(id,name,category,tags))")\
            .eq("table_id", table_id)\
            .gte("created_at", f"{date.today().isoformat()}T00:00:00")\
            .execute().data
        history = history_res

    elif customer_name:
        history_res = supabase.table("orders")\
            .select("id, order_items(menu_item_id, menu_items(id,name,category,tags))")\
            .eq("customer_name", customer_name)\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute().data
        history = history_res

    result = get_recommendations(history, all_items, all_order_items, top_n)
    return result


# ── Forecasting ──────────────────────────────────────────────────────────────

@router.get("/forecast/orders", summary="7-day order volume forecast")
def forecast_orders(days: int = 7, _: str = Depends(verify_admin)):
    # Load last 30 days of daily order counts
    cutoff = (date.today() - timedelta(days=30)).isoformat()
    orders = supabase.table("orders")\
        .select("created_at")\
        .gte("created_at", f"{cutoff}T00:00:00")\
        .execute().data

    daily: dict = defaultdict(int)
    for o in orders:
        d = o["created_at"][:10]
        daily[d] += 1

    return forecast_next_n_days(dict(daily), n=days)


@router.get("/forecast/revenue", summary="7-day revenue forecast")
def forecast_rev(days: int = 7, _: str = Depends(verify_admin)):
    cutoff = (date.today() - timedelta(days=30)).isoformat()
    orders = supabase.table("orders")\
        .select("created_at, total_amount")\
        .eq("status", "served")\
        .gte("created_at", f"{cutoff}T00:00:00")\
        .execute().data

    daily_rev: dict = defaultdict(float)
    for o in orders:
        d = o["created_at"][:10]
        daily_rev[d] += o["total_amount"]

    total_rev   = sum(daily_rev.values())
    order_count = len(orders)
    avg_val     = total_rev / order_count if order_count else 500

    return forecast_revenue(dict(daily_rev), avg_val, n=days)


@router.get("/forecast/peak-hours", summary="Predicted peak hours with load classification")
def forecast_peak(_: str = Depends(verify_admin)):
    orders = supabase.table("orders").select("created_at").execute().data
    from datetime import datetime
    hourly: dict = defaultdict(int)
    for o in orders:
        try:
            h = datetime.fromisoformat(o["created_at"].replace("Z", "+00:00")).hour
            hourly[h] += 1
        except Exception:
            pass
    return peak_hour_forecast(dict(hourly))


# ── Reviews & Sentiment ──────────────────────────────────────────────────────

@router.post("/reviews", status_code=201, summary="Submit a customer review with auto-sentiment")
def submit_review(review: ReviewCreate):
    label, score = analyse_sentiment(review.comment)

    payload = {
        "order_id":       review.order_id,
        "customer_name":  review.customer_name,
        "rating":         review.rating,
        "comment":        review.comment,
        "sentiment":      label,
        "sentiment_score": score,
        "is_published":   True,
    }
    result = supabase.table("reviews").insert(payload).execute()
    return result.data[0]


@router.get("/reviews", summary="Get all published reviews")
def get_reviews(limit: int = 20, offset: int = 0):
    result = supabase.table("reviews")\
        .select("*, orders(customer_name, created_at, tables(table_number))")\
        .eq("is_published", True)\
        .order("created_at", desc=True)\
        .limit(limit).offset(offset)\
        .execute()
    return result.data


@router.get("/reviews/summary", summary="Sentiment analytics summary")
def reviews_summary(_: str = Depends(verify_admin)):
    reviews = supabase.table("reviews")\
        .select("rating, sentiment, sentiment_score, comment")\
        .eq("is_published", True)\
        .execute().data

    if not reviews:
        return {"total": 0, "avg_rating": 0, "distribution": {}}

    total       = len(reviews)
    avg_rating  = sum(r["rating"] for r in reviews) / total
    avg_score   = sum(r.get("sentiment_score") or 0.5 for r in reviews) / total
    dist        = defaultdict(int)
    sent_dist   = defaultdict(int)
    for r in reviews:
        dist[r["rating"]] += 1
        sent_dist[r["sentiment"]] += 1

    return {
        "total":          total,
        "avg_rating":     round(avg_rating, 2),
        "avg_sentiment_score": round(avg_score, 3),
        "rating_distribution":    dict(dist),
        "sentiment_distribution": dict(sent_dist),
        "five_star_pct":  round(dist.get(5, 0) / total * 100, 1),
    }


# ── Menu Insights ────────────────────────────────────────────────────────────

@router.get("/menu-insights", summary="AI-generated menu optimisation insights")
def menu_insights(_: str = Depends(verify_admin)):
    """
    Analyse order data and generate actionable menu insights:
    - Underperforming items
    - High-margin stars
    - Items to promote
    - Items to consider removing
    """
    # Order counts per item
    order_items = supabase.table("order_items")\
        .select("menu_item_id, quantity, unit_price, menu_items(name,category,is_featured,price)")\
        .execute().data

    item_stats: dict = defaultdict(lambda: {"qty": 0, "revenue": 0, "name": "", "category": "", "price": 0})
    for oi in order_items:
        mid = oi["menu_item_id"]
        item_stats[mid]["qty"]     += oi["quantity"]
        item_stats[mid]["revenue"] += oi["quantity"] * oi["unit_price"]
        if oi.get("menu_items"):
            item_stats[mid]["name"]     = oi["menu_items"]["name"]
            item_stats[mid]["category"] = oi["menu_items"]["category"]
            item_stats[mid]["price"]    = oi["menu_items"]["price"]

    if not item_stats:
        return {"insights": [], "message": "Not enough order data yet"}

    avg_qty     = sum(v["qty"] for v in item_stats.values()) / len(item_stats)
    avg_revenue = sum(v["revenue"] for v in item_stats.values()) / len(item_stats)

    insights = []
    for mid, stats in item_stats.items():
        high_orders   = stats["qty"]     > avg_qty     * 1.5
        high_revenue  = stats["revenue"] > avg_revenue * 1.5
        low_orders    = stats["qty"]     < avg_qty     * 0.3
        high_price    = stats["price"]   > 8

        if high_orders and high_revenue:
            insights.append({
                "item":       stats["name"],
                "category":   stats["category"],
                "type":       "star",
                "title":      f"⭐ {stats['name']} is a Star",
                "suggestion": "This item sells well AND earns well. Feature it prominently.",
                "qty":        stats["qty"], "revenue": round(stats["revenue"], 2)
            })
        elif high_orders and not high_revenue:
            insights.append({
                "item":       stats["name"],
                "category":   stats["category"],
                "type":       "plow_horse",
                "title":      f"🔨 {stats['name']} is a Plow Horse",
                "suggestion": "Popular but low margin. Consider a small price increase.",
                "qty":        stats["qty"], "revenue": round(stats["revenue"], 2)
            })
        elif low_orders and high_price:
            insights.append({
                "item":       stats["name"],
                "category":   stats["category"],
                "type":       "dog",
                "title":      f"⚠️ {stats['name']} Under-performs",
                "suggestion": "Low sales + high price. Consider removing or repricing.",
                "qty":        stats["qty"], "revenue": round(stats["revenue"], 2)
            })

    insights.sort(key=lambda x: {"star": 0, "plow_horse": 1, "dog": 2}[x["type"]])
    return {"insights": insights[:15], "items_analysed": len(item_stats)}