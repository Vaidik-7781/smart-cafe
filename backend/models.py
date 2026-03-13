from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


# ── Menu ─────────────────────────────────────────────────────────

class MenuItemCreate(BaseModel):
    name: str
    description: str = ""
    price: float = Field(gt=0)
    category: str
    subcategory: str = ""
    image_url: str = ""
    is_available: bool = True
    is_featured: bool = False
    preparation_time: int = 5
    calories: int = 0
    allergens: List[str] = []
    tags: List[str] = []
    sort_order: int = 0

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    is_featured: Optional[bool] = None
    preparation_time: Optional[int] = None
    calories: Optional[int] = None
    allergens: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    sort_order: Optional[int] = None


# ── Orders ────────────────────────────────────────────────────────

class OrderItemIn(BaseModel):
    menu_item_id: str
    quantity: int = Field(gt=0)
    unit_price: float

class OrderCreate(BaseModel):
    table_id: str
    customer_name: str = "Guest"
    customer_id: Optional[str] = None
    items: List[OrderItemIn]
    subtotal: float
    tax_amount: float
    total_amount: float
    payment_method: str = "cash"
    notes: str = ""

    @field_validator("payment_method")
    @classmethod
    def check_payment(cls, v):
        allowed = {"cash", "card", "upi", "wallet"}
        if v not in allowed:
            raise ValueError(f"payment_method must be one of {allowed}")
        return v

class OrderStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def check_status(cls, v):
        allowed = {"placed", "preparing", "ready", "served", "cancelled"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


# ── Tables ────────────────────────────────────────────────────────

class TableStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def check_status(cls, v):
        allowed = {"available", "occupied", "reserved", "cleaning"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


# ── Reservations ──────────────────────────────────────────────────

class ReservationCreate(BaseModel):
    customer_name: str
    customer_email: str = ""
    customer_phone: str = ""
    table_id: str
    reservation_date: str
    reservation_time: str
    guest_count: int = Field(ge=1, le=20)
    special_requests: str = ""
    source: str = "website"

class ReservationUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def check_status(cls, v):
        allowed = {"confirmed", "cancelled", "completed", "no_show"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


# ── Reviews ───────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    order_id: str
    customer_name: str = "Anonymous"
    rating: int = Field(ge=1, le=5)
    comment: str = ""


# ── Customers ─────────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


# ── Notifications ─────────────────────────────────────────────────

class SendNotificationRequest(BaseModel):
    type: str
    recipient_email: str
    variables: dict = {}

class SendTestEmailRequest(BaseModel):
    template_type: str
    recipient_email: str
    variables: dict = {}


# ── Settings ──────────────────────────────────────────────────────

class SettingUpdate(BaseModel):
    value: str
