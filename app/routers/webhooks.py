import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException
from sqlmodel import Session
from app.database import engine
from app.config import settings
from app.models import Booking, Payment, PaymentStatus

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/paystack")
async def paystack_webhook(request: Request):
    if not settings.paystack_secret_key:
        return {"status": "ignored"}

    raw_body = await request.body()
    signature = request.headers.get("x-paystack-signature")

    expected = hmac.new(
        settings.paystack_secret_key.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    if not signature or not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Invalid signature")

    payload = await request.json()

    if payload.get("event") == "charge.success":
        data = payload.get("data", {})
        reference = data.get("reference")
        amount = data.get("amount")
        booking_id = data.get("metadata", {}).get("booking_id")

        if booking_id:
            with Session(engine) as session:
                booking = session.get(Booking, booking_id)
                if booking and booking.status != "deposit_paid":
                    payment = Payment(
                        booking_id=booking.id,
                        stripe_payment_intent_id=reference,
                        amount_cents=amount,
                        kind="deposit",
                        status=PaymentStatus.succeeded,
                    )
                    session.add(payment)
                    booking.status = "deposit_paid"
                    session.add(booking)
                    session.commit()

    return {"status": "success"}