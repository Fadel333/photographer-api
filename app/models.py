from datetime import datetime, date, time, timezone
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class EventType(str, Enum):
    wedding = "wedding"
    funeral = "funeral"
    birthday = "birthday"
    photoshoot = "photoshoot"
    other = "other"


class BookingStatus(str, Enum):
    inquiry = "inquiry"
    contacted = "contacted"
    confirmed = "confirmed"
    deposit_paid = "deposit_paid"
    completed = "completed"
    cancelled = "cancelled"


class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded"


class Admin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Package(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: EventType
    name: str
    description: str = ""
    price_cents: int
    deposit_pct: int = 30
    duration_hours: int = 4
    active: bool = True


class BlockedDate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    start_date: date
    end_date: date
    reason: str = ""


class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_name: str
    customer_email: str = Field(index=True)
    customer_phone: str = ""
    event_type: EventType
    event_date: date
    start_time: Optional[time] = None
    duration_hours: int = 4
    location: str = ""
    package_id: Optional[int] = Field(default=None, foreign_key="package.id")
    notes: str = ""
    status: BookingStatus = BookingStatus.inquiry
    terms_version: str = "v1"
    terms_accepted_at: Optional[datetime] = None
    total_cents: int = 0
    deposit_cents: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payments: List["Payment"] = Relationship(back_populates="booking")


class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="booking.id")
    stripe_payment_intent_id: str = Field(index=True, unique=True)
    amount_cents: int
    kind: str = "deposit"
    status: PaymentStatus = PaymentStatus.pending
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    booking: Optional[Booking] = Relationship(back_populates="payments")