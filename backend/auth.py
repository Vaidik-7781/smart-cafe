"""
auth.py — Authentication helpers.
Currently uses a simple shared admin token (header: x-admin-token).
Extendable to full JWT in production.
"""
from fastapi import HTTPException, Header, Depends
from config import settings


def verify_admin(x_admin_token: str = Header(...)) -> str:
    """Dependency: require valid admin token."""
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden: invalid admin token")
    return x_admin_token


def optional_admin(x_admin_token: str = Header(default="")) -> bool:
    """Dependency: returns True if admin token present and valid."""
    return x_admin_token == settings.ADMIN_TOKEN