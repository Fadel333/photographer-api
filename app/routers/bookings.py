from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
import requests

from app.database import get_session
from app.deps import get_current_admin
from app.models import Booking, Package, BlockedDate, BookingStatus
from app.schemas import BookingInquiryIn, BookingOut
from app.config import settings

try:
    import resend
    if settings.resend_api_key:
        resend.api_key = settings.resend_api_key
except ImportError:
    resend = None


router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/inquiry", response_model=BookingOut)
def create_inquiry(data: BookingInquiryIn, session: Session = Depends(get_session)):
    if not data.terms_accepted:
        raise HTTPException(400, "Terms must be accepted")

    conflict = session.exec(
        select(BlockedDate).where(
            BlockedDate.start_date <= data.event_date,
            BlockedDate.end_date >= data.event_date,
        )
    ).first()
    if conflict:
        raise HTTPException(409, f"Date unavailable: {conflict.reason or 'blocked'}")

    total = deposit = 0
    if data.package_id:
        pkg = session.get(Package, data.package_id)
        if not pkg:
            raise HTTPException(404, "Package not found")
        total = pkg.price_cents
        deposit = int(total * pkg.deposit_pct / 100)

    booking = Booking(
        **data.model_dump(exclude={"terms_accepted"}),
        total_cents=total,
        deposit_cents=deposit,
        terms_accepted_at=datetime.now(timezone.utc),
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)

    if resend and settings.resend_api_key and settings.photographer_email:
        try:
            resend.Emails.send({
                "from": "onboarding@resend.dev",
                "to": settings.photographer_email,
                "subject": f"New {booking.event_type} inquiry — {booking.event_date}",
                "html": (
                    f"<p><b>{booking.customer_name}</b> ({booking.customer_email})</p>"
                    f"<p>{booking.event_type} on {booking.event_date} · {booking.location or 'location TBD'}</p>"
                ),
            })
        except Exception as e:
            print("Email failed:", e)

    return booking


@router.get("", response_model=list[BookingOut], dependencies=[Depends(get_current_admin)])
def list_bookings(session: Session = Depends(get_session)):
    return session.exec(select(Booking).order_by(Booking.created_at.desc())).all()


# NEW: Public endpoint for the success page (no admin auth required)
@router.get("/{booking_id}/public", response_model=BookingOut)
def get_booking_public(booking_id: int, session: Session = Depends(get_session)):
    b = session.get(Booking, booking_id)
    if not b:
        raise HTTPException(404, "Booking not found")
    return b


@router.patch("/{booking_id}/status", response_model=BookingOut,
              dependencies=[Depends(get_current_admin)])
def set_status(booking_id: int, status: BookingStatus,
               session: Session = Depends(get_session)):
    b = session.get(Booking, booking_id)
    if not b:
        raise HTTPException(404, "Not found")
    b.status = status
    b.updated_at = datetime.now(timezone.utc)
    session.add(b)
    session.commit()
    session.refresh(b)
    return b

from pydantic import BaseModel

class QuoteIn(BaseModel):
    total_cents: int
    deposit_pct: int = 30


@router.patch("/{booking_id}/quote", response_model=BookingOut,
              dependencies=[Depends(get_current_admin)])
def set_quote(booking_id: int, data: QuoteIn,
              session: Session = Depends(get_session)):
    b = session.get(Booking, booking_id)
    if not b:
        raise HTTPException(404, "Not found")
    if data.total_cents <= 0:
        raise HTTPException(400, "Total must be greater than 0")
    if data.deposit_pct < 1 or data.deposit_pct > 100:
        raise HTTPException(400, "Deposit % must be between 1 and 100")

    b.total_cents = data.total_cents
    b.deposit_cents = int(data.total_cents * data.deposit_pct / 100)
    b.status = BookingStatus.confirmed
    b.updated_at = datetime.now(timezone.utc)
    session.add(b)
    session.commit()
    session.refresh(b)
    return b


@router.post("/{booking_id}/deposit")
def create_deposit(booking_id: int, session: Session = Depends(get_session)):
    if not settings.paystack_secret_key:
        raise HTTPException(500, "Paystack is not configured on the server")

    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    if booking.deposit_cents <= 0:
        raise HTTPException(400, "No deposit required for this booking")
    if booking.status not in ["inquiry", "confirmed"]:
        raise HTTPException(400, "Booking is not in a state to accept deposits")

    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.paystack_secret_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": booking.customer_email,
        "amount": booking.deposit_cents,
        "currency": "GHS",
        "metadata": {"booking_id": booking.id},
        "callback_url": "http://localhost:3000/book/success",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"PAYSTACK RAW RESPONSE: {response.status_code} - {response.text}")
        
        if response.status_code != 200:
            raise HTTPException(500, f"Paystack HTTP Error {response.status_code}: {response.text}")

        data = response.json()
        
        if not data.get("status"):
            raise HTTPException(500, f"Paystack API Error: {data.get('message')}")

        return {
            "authorization_url": data["data"]["authorization_url"],
            "reference": data["data"]["reference"],
        }
    except requests.RequestException as e:
        print(f"PAYSTACK NETWORK FAIL: {str(e)}")
        raise HTTPException(500, f"Payment provider unreachable: {str(e)}")