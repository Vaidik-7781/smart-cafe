"""
routers/menu.py — Menu CRUD, image upload via Cloudinary, category management.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional, List
from datetime import datetime
import httpx

from database import supabase
from auth import verify_admin
from models import MenuItemCreate, MenuItemUpdate
from config import settings

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.get("", summary="Public: get all available menu items")
def get_menu(category: Optional[str] = None, featured: Optional[bool] = None):
    query = supabase.table("menu_items").select("*").eq("is_available", True)
    if category:
        query = query.eq("category", category)
    if featured is not None:
        query = query.eq("is_featured", featured)
    result = query.order("sort_order").order("category").execute()
    return result.data


@router.get("/all", summary="Admin: get all items including unavailable")
def get_all_menu(_: str = Depends(verify_admin)):
    result = supabase.table("menu_items").select("*").order("category").order("sort_order").execute()
    return result.data


@router.get("/categories", summary="Get distinct categories")
def get_categories():
    result = supabase.table("menu_items").select("category").eq("is_available", True).execute()
    cats = sorted(set(r["category"] for r in result.data))
    return cats


@router.get("/search", summary="Search menu items by name or description")
def search_menu(q: str):
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    result = supabase.table("menu_items").select("*").eq("is_available", True)\
        .or_(f"name.ilike.%{q}%,description.ilike.%{q}%,tags.cs.{{{q}}}")\
        .execute()
    return result.data


@router.get("/{item_id}", summary="Get single menu item")
def get_menu_item(item_id: str):
    try:
        result = supabase.table("menu_items").select("*").eq("id", item_id).single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return result.data


@router.post("", status_code=201, summary="Admin: create menu item")
def create_menu_item(item: MenuItemCreate, _: str = Depends(verify_admin)):
    payload = item.model_dump()
    payload["created_at"] = datetime.utcnow().isoformat()
    result = supabase.table("menu_items").insert(payload).execute()
    return result.data[0]


@router.put("/{item_id}", summary="Admin: update menu item")
def update_menu_item(item_id: str, item: MenuItemUpdate, _: str = Depends(verify_admin)):
    updates = {k: v for k, v in item.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = datetime.utcnow().isoformat()
    try:
        result = supabase.table("menu_items").update(updates).eq("id", item_id).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.data:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return result.data[0]


@router.patch("/{item_id}/toggle", summary="Admin: toggle item availability")
def toggle_availability(item_id: str, _: str = Depends(verify_admin)):
    try:
        current = supabase.table("menu_items").select("is_available").eq("id", item_id).single().execute()
        new_val = not current.data["is_available"]
        result = supabase.table("menu_items").update({"is_available": new_val}).eq("id", item_id).execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, "is_available": new_val}


@router.delete("/{item_id}", summary="Admin: delete menu item")
def delete_menu_item(item_id: str, _: str = Depends(verify_admin)):
    supabase.table("menu_items").delete().eq("id", item_id).execute()
    return {"message": "Item deleted", "id": item_id}


@router.post("/{item_id}/upload-image", summary="Admin: upload image to Cloudinary")
async def upload_image(item_id: str, file: UploadFile = File(...), _: str = Depends(verify_admin)):
    """Upload a menu item image to Cloudinary and save URL to DB."""
    if not settings.CLOUDINARY_CLOUD_NAME:
        raise HTTPException(status_code=503, detail="Cloudinary not configured (add CLOUDINARY_* to .env)")

    contents = await file.read()
    upload_url = f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}/image/upload"

    async with httpx.AsyncClient() as client:
        resp = await client.post(upload_url, data={
            "upload_preset": settings.CLOUDINARY_UPLOAD_PRESET,
            "folder": "smart_cafe/menu",
        }, files={"file": (file.filename, contents, file.content_type)})

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Cloudinary upload failed")

    image_url = resp.json()["secure_url"]
    supabase.table("menu_items").update({"image_url": image_url}).eq("id", item_id).execute()
    return {"image_url": image_url}