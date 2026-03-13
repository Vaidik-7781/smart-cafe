"""
routers/orders.py — Order lifecycle: place, track, kitchen, status updates.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime

from database import supabase
from auth import verify_admin
from models import OrderCreate, OrderStatusUpdate
from config import settings

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", status_code=201, summary="Place a new order")
def place_order(order: OrderCreate):
    """
    Place order from customer.
    - Inserts order row
    - Inserts all order_item rows
    - Marks table as occupied
    """
    # 1. Verify table exists
    table = supabase.table("tables").select("id,status").eq("id", order.table_id).execute()
    if not table.data:
        raise HTTPException(status_code=404, detail="Table not found")

    # 2. Insert order
    payload = {
        "table_id":       order.table_id,
        "customer_name":  order.customer_name,
        "customer_id":    order.customer_id,
        "status":         "placed",
        "payment_method": order.payment_method,
        "payment_status": "pending",
        "subtotal":       order.subtotal,
        "tax_amount":     order.tax_amount,
        "total_amount":   order.total_amount,
        "notes":          order.notes,
        "created_at":     datetime.utcnow().isoformat(),
    }
    order_res = supabase.table("orders").insert(payload).execute()
    order_id = order_res.data[0]["id"]

    # 3. Insert order items
    items_payload = [
        {
            "order_id":     order_id,
            "menu_item_id": it.menu_item_id,
            "quantity":     it.quantity,
            "unit_price":   it.unit_price,
        }
        for it in order.items
    ]
    supabase.table("order_items").insert(items_payload).execute()

    # 4. Mark table as occupied
    supabase.table("tables").update({
        "status": "occupied",
        "current_order_id": order_id,
        "last_occupied": datetime.utcnow().isoformat()
    }).eq("id", order.table_id).execute()

    return {
        "order_id": order_id,
        "status": "placed",
        "message": "Order placed successfully! Kitchen notified."
    }


@router.get("/kitchen", summary="Kitchen: active orders (placed + preparing)")
def get_kitchen_orders():
    result = supabase.table("orders")\
        .select("*, order_items(*, menu_items(id,name,image_url,preparation_time)), tables(table_number,zone)")\
        .in_("status", ["placed", "preparing"])\
        .order("created_at")\
        .execute()
    return result.data


@router.get("", summary="Admin: list all orders")
def get_all_orders(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _: str = Depends(verify_admin)
):
    query = supabase.table("orders")\
        .select("*, order_items(*, menu_items(name,image_url)), tables(table_number)")\
        .order("created_at", desc=True)\
        .limit(limit)\
        .offset(offset)
    if status:
        query = query.eq("status", status)
    return query.execute().data


@router.get("/table/{table_id}", summary="Get active orders for a table")
def get_orders_by_table(table_id: str):
    result = supabase.table("orders")\
        .select("*, order_items(*, menu_items(name,image_url))")\
        .eq("table_id", table_id)\
        .not_.eq("status", "served")\
        .not_.eq("status", "cancelled")\
        .order("created_at", desc=True)\
        .execute()
    return result.data


@router.get("/{order_id}", summary="Get single order with items")
def get_order(order_id: str):
    try:
        order = supabase.table("orders")\
            .select("*, tables(table_number, zone)")\
            .eq("id", order_id).single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Order not found")

    items = supabase.table("order_items")\
        .select("*, menu_items(id,name,description,image_url,category)")\
        .eq("order_id", order_id).execute()

    return {**order.data, "order_items": items.data}


@router.put("/{order_id}/status", summary="Update order status")
def update_order_status(order_id: str, body: OrderStatusUpdate):
    try:
        result = supabase.table("orders")\
            .update({"status": body.status})\
            .eq("id", order_id).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.data:
        raise HTTPException(status_code=404, detail="Order not found")

    order = result.data[0]

    # Free table when served
    if body.status == "served" and order.get("table_id"):
        supabase.table("tables").update({
            "status": "available",
            "current_order_id": None
        }).eq("id", order["table_id"]).execute()

    # Update payment status when served
    if body.status == "served":
        supabase.table("orders").update({"payment_status": "paid"})\
            .eq("id", order_id).execute()

    return order


@router.put("/{order_id}/payment", summary="Update payment status")
def update_payment(order_id: str, payment_method: str, _: str = Depends(verify_admin)):
    valid = {"cash", "card", "upi", "wallet"}
    if payment_method not in valid:
        raise HTTPException(status_code=400, detail=f"Must be one of {valid}")
    result = supabase.table("orders").update({
        "payment_method": payment_method,
        "payment_status": "paid"
    }).eq("id", order_id).execute()
    return result.data[0] if result.data else {}


@router.delete("/{order_id}", summary="Admin: cancel order")
def cancel_order(order_id: str, _: str = Depends(verify_admin)):
    # Get order first for table_id
    order = supabase.table("orders").select("table_id").eq("id", order_id).execute()
    if not order.data:
        raise HTTPException(status_code=404, detail="Order not found")
    table_id = order.data[0].get("table_id")

    # Cancel order
    supabase.table("orders").update({"status": "cancelled"}).eq("id", order_id).execute()

    # Free table
    if table_id:
        supabase.table("tables").update({
            "status": "available",
            "current_order_id": None
        }).eq("id", table_id).execute()

    return {"message": "Order cancelled", "order_id": order_id}