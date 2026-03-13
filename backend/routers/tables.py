"""
routers/tables.py — Table management, QR code URL generation.
"""
from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from auth import verify_admin
from models import TableStatusUpdate
from config import settings

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.get("", summary="Get all tables with current status")
def get_tables():
    result = supabase.table("tables")\
        .select("*, orders(id,status,customer_name,total_amount,created_at)")\
        .order("table_number")\
        .execute()

    tables = result.data
    for t in tables:
        # Only include active orders
        active_orders = [o for o in (t.get("orders") or [])
                         if o.get("status") not in ("served", "cancelled")]
        t["active_order"] = active_orders[0] if active_orders else None
        t.pop("orders", None)
        # Build QR URL pointing to menu page
        frontend_url = settings.FRONTEND_URL
        t["qr_url"] = f"{frontend_url}/menu.html?table_id={t['id']}&table={t['table_number']}"
    return tables


@router.get("/zones", summary="Get tables grouped by zone")
def get_tables_by_zone():
    result = supabase.table("tables").select("*").order("zone").order("table_number").execute()
    zones: dict = {}
    for t in result.data:
        z = t["zone"]
        zones.setdefault(z, []).append(t)
    return zones


@router.get("/{table_id}", summary="Get single table")
def get_table(table_id: str):
    try:
        result = supabase.table("tables").select("*").eq("id", table_id).single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Table not found")
    return result.data


@router.put("/{table_id}", summary="Update table status")
def update_table(table_id: str, body: TableStatusUpdate, _: str = Depends(verify_admin)):
    try:
        result = supabase.table("tables").update({"status": body.status})\
            .eq("id", table_id).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.data:
        raise HTTPException(status_code=404, detail="Table not found")
    return result.data[0]


@router.post("/{table_id}/reset", summary="Reset table to available + clear order reference")
def reset_table(table_id: str, _: str = Depends(verify_admin)):
    result = supabase.table("tables").update({
        "status": "available",
        "current_order_id": None
    }).eq("id", table_id).execute()
    return result.data[0] if result.data else {"message": "Cleared"}