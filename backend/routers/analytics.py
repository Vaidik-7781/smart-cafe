"""
routers/analytics.py — All analytics endpoints:
  daily-sales, weekly-sales, peak-hours, popular-items,
  revenue-by-category, customer-stats, staffing recommendations.
"""
from fastapi import APIRouter, Depends
from typing import Optional
from datetime import datetime, date, timedelta
from collections import defaultdict

from database import supabase
from auth import verify_admin

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _get_served_orders(days: int = 30):
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    return supabase.table("orders")\
        .select("id, total_amount, subtotal, created_at, served_at, payment_method")\
        .eq("status", "served")\
        .gte("created_at", cutoff)\
        .execute().data


@router.get("/daily-sales", summary="Today's sales summary")
def daily_sales(_: str = Depends(verify_admin)):
    today = date.today().isoformat()
    result = supabase.table("orders")\
        .select("total_amount, subtotal, tax_amount, created_at, payment_method")\
        .eq("status", "served")\
        .gte("created_at", f"{today}T00:00:00")\
        .lte("created_at", f"{today}T23:59:59")\
        .execute()

    orders = result.data
    total     = sum(o["total_amount"] for o in orders)
    subtotal  = sum(o.get("subtotal", 0) for o in orders)
    tax_total = sum(o.get("tax_amount", 0) for o in orders)

    # Payment breakdown
    payments: dict = defaultdict(float)
    for o in orders:
        payments[o.get("payment_method", "unknown")] += o["total_amount"]

    return {
        "date":           today,
        "total_revenue":  round(total, 2),
        "subtotal":       round(subtotal, 2),
        "tax_collected":  round(tax_total, 2),
        "order_count":    len(orders),
        "avg_order_value": round(total / len(orders), 2) if orders else 0,
        "payment_breakdown": dict(payments),
    }


@router.get("/weekly-sales", summary="Sales by day for past 7 days")
def weekly_sales(_: str = Depends(verify_admin)):
    cutoff = (date.today() - timedelta(days=6)).isoformat()
    result = supabase.table("orders")\
        .select("total_amount, created_at")\
        .eq("status", "served")\
        .gte("created_at", f"{cutoff}T00:00:00")\
        .execute()

    days: dict = defaultdict(lambda: {"sales": 0.0, "orders": 0})
    for o in result.data:
        d = o["created_at"][:10]
        days[d]["sales"]  += o["total_amount"]
        days[d]["orders"] += 1

    # Fill in 0s for days with no orders
    all_days = []
    for i in range(7):
        d = (date.today() - timedelta(days=6-i)).isoformat()
        all_days.append({
            "date":   d,
            "sales":  round(days[d]["sales"], 2),
            "orders": days[d]["orders"]
        })
    return all_days


@router.get("/monthly-sales", summary="Sales by day for past 30 days")
def monthly_sales(_: str = Depends(verify_admin)):
    orders = _get_served_orders(30)
    days: dict = defaultdict(lambda: {"sales": 0.0, "orders": 0})
    for o in orders:
        d = o["created_at"][:10]
        days[d]["sales"]  += o["total_amount"]
        days[d]["orders"] += 1
    result = []
    for i in range(30):
        d = (date.today() - timedelta(days=29-i)).isoformat()
        result.append({"date": d, "sales": round(days[d]["sales"], 2), "orders": days[d]["orders"]})
    return result


@router.get("/peak-hours", summary="Order volume by hour of day (avg)")
def peak_hours(_: str = Depends(verify_admin)):
    result = supabase.table("orders").select("created_at").execute()
    hours: dict = defaultdict(int)
    for row in result.data:
        try:
            h = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")).hour
            hours[h] += 1
        except Exception:
            pass
    return [{"hour": f"{h:02d}:00", "label": f"{h}{'am' if h<12 else 'pm'}", "orders": hours.get(h, 0)} for h in range(24)]


@router.get("/popular-items", summary="Top 10 most ordered items")
def popular_items(_: str = Depends(verify_admin)):
    result = supabase.table("order_items")\
        .select("menu_item_id, quantity, unit_price, menu_items(name, category, image_url)")\
        .execute()

    counts: dict = defaultdict(lambda: {"qty": 0, "revenue": 0.0, "name": "", "category": "", "image_url": ""})
    for row in result.data:
        mid = row["menu_item_id"]
        if row.get("menu_items"):
            counts[mid]["name"]      = row["menu_items"]["name"]
            counts[mid]["category"]  = row["menu_items"]["category"]
            counts[mid]["image_url"] = row["menu_items"].get("image_url", "")
        counts[mid]["qty"]     += row["quantity"]
        counts[mid]["revenue"] += row["quantity"] * row["unit_price"]

    sorted_items = sorted(counts.items(), key=lambda x: x[1]["qty"], reverse=True)
    return [{"menu_item_id": k, **v, "revenue": round(v["revenue"], 2)} for k, v in sorted_items[:10]]


@router.get("/revenue-by-category", summary="Revenue breakdown by menu category")
def revenue_by_category(_: str = Depends(verify_admin)):
    result = supabase.table("order_items")\
        .select("quantity, unit_price, menu_items(category)")\
        .execute()

    cats: dict = defaultdict(float)
    for row in result.data:
        cat = (row.get("menu_items") or {}).get("category", "Unknown")
        cats[cat] += row["quantity"] * row["unit_price"]

    total = sum(cats.values()) or 1
    return [
        {"category": k, "revenue": round(v, 2), "pct": round(v / total * 100, 1)}
        for k, v in sorted(cats.items(), key=lambda x: x[1], reverse=True)
    ]


@router.get("/customer-stats", summary="Customer acquisition and repeat stats")
def customer_stats(_: str = Depends(verify_admin)):
    orders = supabase.table("orders").select("customer_name, total_amount, created_at")\
        .eq("status", "served").execute().data

    customers: dict = defaultdict(lambda: {"visits": 0, "spent": 0.0, "first": None, "last": None})
    for o in orders:
        name = o["customer_name"]
        customers[name]["visits"] += 1
        customers[name]["spent"]  += o["total_amount"]
        ts = o["created_at"]
        if not customers[name]["first"] or ts < customers[name]["first"]:
            customers[name]["first"] = ts
        if not customers[name]["last"]  or ts > customers[name]["last"]:
            customers[name]["last"] = ts

    repeat = sum(1 for c in customers.values() if c["visits"] > 1)
    return {
        "total_unique_customers": len(customers),
        "repeat_customers":       repeat,
        "repeat_rate_pct":        round(repeat / len(customers) * 100, 1) if customers else 0,
        "top_customers": sorted(
            [{"name": k, **v} for k, v in customers.items()],
            key=lambda x: x["spent"], reverse=True
        )[:10]
    }


@router.get("/staffing-recommendations", summary="AI staffing recommendations based on peak hours")
def staffing_recommendations(_: str = Depends(verify_admin)):
    """
    Analyse peak-hour data and return shift recommendations.
    """
    orders = supabase.table("orders").select("created_at").execute().data
    hours: dict = defaultdict(int)
    for row in orders:
        try:
            h = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")).hour
            hours[h] += 1
        except Exception:
            pass

    max_orders = max(hours.values()) if hours else 1

    recommendations = []
    shifts = [
        {"label": "Morning",   "hours": range(6, 12),  "base_staff": 2},
        {"label": "Afternoon", "hours": range(12, 17), "base_staff": 3},
        {"label": "Evening",   "hours": range(17, 22), "base_staff": 3},
    ]

    for shift in shifts:
        volume = sum(hours.get(h, 0) for h in shift["hours"])
        load   = volume / (max_orders * len(list(shift["hours"]))) if max_orders else 0
        extra  = max(0, round((load - 0.5) * 4))
        recommendations.append({
            "shift":              shift["label"],
            "hours":              f"{min(shift['hours']):02d}:00–{max(shift['hours'])+1:02d}:00",
            "avg_orders_per_hr":  round(volume / len(list(shift["hours"])), 1),
            "recommended_staff":  shift["base_staff"] + extra,
            "load_level":         "high" if load > 0.7 else "medium" if load > 0.4 else "low",
        })
    return recommendations


@router.get("/summary", summary="Full analytics dashboard summary (single request)")
def summary(_: str = Depends(verify_admin)):
    """Aggregate endpoint — returns everything the dashboard needs in one call."""
    from routers.analytics import daily_sales as _daily, popular_items as _popular

    today_obj = date.today()
    today     = today_obj.isoformat()
    yesterday = (today_obj - timedelta(days=1)).isoformat()

    # Today
    today_orders = supabase.table("orders")\
        .select("total_amount")\
        .eq("status","served")\
        .gte("created_at", f"{today}T00:00:00").execute().data
    today_rev = sum(o["total_amount"] for o in today_orders)

    # Yesterday
    yest_orders = supabase.table("orders")\
        .select("total_amount")\
        .eq("status","served")\
        .gte("created_at", f"{yesterday}T00:00:00")\
        .lte("created_at", f"{yesterday}T23:59:59").execute().data
    yest_rev = sum(o["total_amount"] for o in yest_orders) or 1

    # Active orders
    active = supabase.table("orders")\
        .select("id").in_("status",["placed","preparing","ready"]).execute().data

    # Occupancy
    occ = supabase.table("tables").select("status").execute().data
    occ_count   = sum(1 for t in occ if t["status"] == "occupied")
    total_tables = len(occ)

    # Reviews average
    rev_avg = supabase.table("reviews").select("rating").execute().data
    avg_rating = round(sum(r["rating"] for r in rev_avg) / len(rev_avg), 1) if rev_avg else 0

    return {
        "today": {
            "revenue":      round(today_rev, 2),
            "order_count":  len(today_orders),
            "revenue_vs_yesterday_pct": round((today_rev - yest_rev) / yest_rev * 100, 1) if yest_rev else 0,
        },
        "active_orders": len(active),
        "table_occupancy": {
            "occupied":   occ_count,
            "total":      total_tables,
            "pct":        round(occ_count / total_tables * 100, 1) if total_tables else 0,
        },
        "avg_rating": avg_rating,
    }