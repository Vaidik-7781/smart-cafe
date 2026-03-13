"""
routers/reservations.py — Reservation CRUD, conflict detection, time slot availability.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, date

from database import supabase
from auth import verify_admin
from models import ReservationCreate, ReservationUpdate

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("", status_code=201, summary="Create a reservation")
def create_reservation(res: ReservationCreate):
    # 1. Conflict check: same table, same date, overlapping time (±2h window)
    conflict = supabase.table("reservations")\
        .select("id")\
        .eq("table_id",         res.table_id)\
        .eq("reservation_date", res.reservation_date)\
        .eq("reservation_time", res.reservation_time)\
        .in_("status",          ["confirmed"])\
        .execute()

    if conflict.data:
        raise HTTPException(
            status_code=409,
            detail="This table is already reserved for that time slot. "
                   "Please choose a different table or time."
        )

    # 2. Verify table capacity
    table = supabase.table("tables")\
        .select("capacity,table_number")\
        .eq("id", res.table_id).execute()
    if not table.data:
        raise HTTPException(status_code=404, detail="Table not found")
    if table.data[0]["capacity"] < res.guest_count:
        raise HTTPException(
            status_code=422,
            detail=f"Table {table.data[0]['table_number']} only fits "
                   f"{table.data[0]['capacity']} guests. You requested {res.guest_count}."
        )

    # 3. Insert reservation
    payload = res.model_dump()
    payload["status"]     = "confirmed"
    payload["created_at"] = datetime.utcnow().isoformat()

    result = supabase.table("reservations").insert(payload).execute()

    # 4. Mark table as reserved
    supabase.table("tables").update({"status": "reserved"})\
        .eq("id", res.table_id).execute()

    return result.data[0]


@router.get("", summary="Admin: list reservations")
def get_reservations(
    res_date: Optional[str] = None,
    status: Optional[str] = None,
    _: str = Depends(verify_admin)
):
    query = supabase.table("reservations")\
        .select("*, tables(table_number, capacity, zone)")\
        .order("reservation_date")\
        .order("reservation_time")
    if res_date:
        query = query.eq("reservation_date", res_date)
    if status:
        query = query.eq("status", status)
    return query.execute().data


@router.get("/availability", summary="Check available tables for date/time/guests")
def check_availability(
    res_date: str,
    res_time: str,
    guest_count: int = 2
):
    """Return tables that are free for the given date/time/guest_count."""
    # All tables with enough capacity
    all_tables = supabase.table("tables")\
        .select("*")\
        .gte("capacity", guest_count)\
        .execute().data

    # Already reserved for that slot
    booked = supabase.table("reservations")\
        .select("table_id")\
        .eq("reservation_date", res_date)\
        .eq("reservation_time", res_time)\
        .in_("status", ["confirmed"])\
        .execute().data

    booked_ids = {r["table_id"] for r in booked}
    available = [t for t in all_tables if t["id"] not in booked_ids]
    return available


@router.get("/upcoming", summary="Get today's and upcoming reservations")
def upcoming_reservations(_: str = Depends(verify_admin)):
    today = date.today().isoformat()
    result = supabase.table("reservations")\
        .select("*, tables(table_number, zone)")\
        .gte("reservation_date", today)\
        .in_("status", ["confirmed"])\
        .order("reservation_date").order("reservation_time")\
        .limit(20)\
        .execute()
    return result.data


@router.get("/{res_id}", summary="Get single reservation")
def get_reservation(res_id: str, _: str = Depends(verify_admin)):
    try:
        result = supabase.table("reservations")\
            .select("*, tables(table_number, capacity, zone)")\
            .eq("id", res_id).single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return result.data


@router.put("/{res_id}", summary="Update reservation status")
def update_reservation(res_id: str, body: ReservationUpdate, _: str = Depends(verify_admin)):
    try:
        result = supabase.table("reservations")\
            .update({"status": body.status})\
            .eq("id", res_id).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.data:
        raise HTTPException(status_code=404, detail="Reservation not found")

    reservation = result.data[0]

    # Free table on cancel/complete
    if body.status in ("cancelled", "completed") and reservation.get("table_id"):
        supabase.table("tables").update({"status": "available"})\
            .eq("id", reservation["table_id"]).execute()

    return reservation