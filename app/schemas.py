from datetime import datetime, date, time
from pydantic import BaseModel, EmailStr
from app.models import EventType, BookingStatus, PaymentStatus

class PackageIn(BaseModel):
    event_type: EventType
    name: str
    description: str = ""
    price_cents: int
    deposit_pct: int = 30
    duration_hours: int = 4

class PackageOut(PackageIn):
    id: int
    active: bool
    model_config = {"from_attributes": True}

class BookingInquiryIn(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_phone: str = ""
    event_type: EventType
    event_date: date
    start_time: time | None = None
    duration_hours: int = 4
    location: str = ""
    package_id: int | None = None
    notes: str = ""
    terms_accepted: bool

class BookingOut(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    event_type: EventType
    event_date: date
    status: BookingStatus
    total_cents: int
    deposit_cents: int
    model_config = {"from_attributes": True}

class PaymentOut(BaseModel):
    id: int
    amount_cents: int
    kind: str
    status: PaymentStatus
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"