"""
routers/customers.py — Customer management, loyalty points, visit history.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from database import supabase
from auth import verify_admin
from models import CustomerCreate

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", summary="Admin: list all customers")
def list_customers(limit: int = 50, offset: int = 0, _: str = Depends(verify_admin)):
    return supabase.table("customers").select("*")\
        .order("total_spent", desc=True)\
        .limit(limit).offset(offset).execute().data


@router.post("", status_code=201, summary="Register / upsert customer")
def upsert_customer(customer: CustomerCreate):
    if customer.email:
        existing = supabase.table("customers").select("*")\
            .eq("email", customer.email).execute()
        if existing.data:
            return existing.data[0]

    result = supabase.table("customers").insert(customer.model_dump()).execute()
    return result.data[0]


@router.get("/{customer_id}", summary="Get single customer with order history")
def get_customer(customer_id: str, _: str = Depends(verify_admin)):
    try:
        customer = supabase.table("customers").select("*").eq("id", customer_id).single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Customer not found")

    orders = supabase.table("orders")\
        .select("id, status, total_amount, created_at, tables(table_number)")\
        .eq("customer_id", customer_id)\
        .order("created_at", desc=True)\
        .limit(20).execute().data

    points = supabase.table("loyalty_points")\
        .select("points, description, created_at")\
        .eq("customer_id", customer_id)\
        .order("created_at", desc=True)\
        .limit(10).execute().data

    total_points = sum(p["points"] for p in points)

    return {
        **customer.data,
        "order_history":  orders,
        "loyalty_points_log": points,
        "current_points": total_points,
    }


@router.get("/{customer_id}/loyalty", summary="Get customer loyalty point balance")
def loyalty_balance(customer_id: str):
    points = supabase.table("loyalty_points")\
        .select("points").eq("customer_id", customer_id).execute().data
    total = sum(p["points"] for p in points)
    return {"customer_id": customer_id, "points": total, "redeemable_value": round(total * 0.10, 2)}


@router.post("/{customer_id}/loyalty/redeem", summary="Redeem loyalty points")
def redeem_points(customer_id: str, points: int):
    balance_res = supabase.table("loyalty_points")\
        .select("points").eq("customer_id", customer_id).execute().data
    balance = sum(p["points"] for p in balance_res)
    if points > balance:
        raise HTTPException(status_code=400, detail=f"Insufficient points. Balance: {balance}")
    supabase.table("loyalty_points").insert({
        "customer_id": customer_id,
        "points":      -points,
        "description": f"Redeemed {points} points"
    }).execute()
    return {"redeemed": points, "remaining": balance - points, "value": round(points * 0.10, 2)}