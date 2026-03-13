"""
routers/settings.py — Cafe-wide settings and Cloudinary signed upload.
"""
from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from auth import verify_admin
from models import SettingUpdate
from config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", summary="Get all cafe settings (public)")
def get_settings():
    result = supabase.table("cafe_settings").select("*").execute()
    return {row["key"]: row["value"] for row in result.data}


@router.get("/{key}", summary="Get a single setting by key")
def get_setting(key: str):
    try:
        result = supabase.table("cafe_settings").select("value").eq("key", key).single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return {"key": key, "value": result.data["value"]}


@router.put("/{key}", summary="Admin: update a cafe setting")
def update_setting(key: str, body: SettingUpdate, _: str = Depends(verify_admin)):
    result = supabase.table("cafe_settings").upsert({"key": key, "value": body.value}).execute()
    return {"key": key, "value": body.value}


@router.get("/cloudinary/sign", summary="Get Cloudinary signed upload params")
def cloudinary_sign(_: str = Depends(verify_admin)):
    """
    Returns the cloud_name and unsigned upload_preset for direct browser uploads.
    For production, generate a signed upload here using Cloudinary's Python SDK.
    """
    if not settings.CLOUDINARY_CLOUD_NAME:
        raise HTTPException(status_code=503, detail="Cloudinary not configured")
    return {
        "cloud_name":     settings.CLOUDINARY_CLOUD_NAME,
        "upload_preset":  settings.CLOUDINARY_UPLOAD_PRESET,
        "upload_url":     f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}/image/upload",
        "folder":         "smart_cafe/menu",
    }