from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.deps import get_current_admin
from app.models import BlockedDate, Booking

router = APIRouter(prefix="/blocked-dates", tags=["availability"])

@router.get("", response_model=list[BlockedDate])
def list_blocked(session: Session = Depends(get_session)):
    return session.exec(select(BlockedDate).order_by(BlockedDate.start_date)).all()

@router.post("", response_model=BlockedDate, dependencies=[Depends(get_current_admin)])
def create_blocked(data: BlockedDate, session: Session = Depends(get_session)):
    if data.end_date < data.start_date:
        raise HTTPException(400, "end_date must be >= start_date")
    session.add(data); session.commit(); session.refresh(data)
    return data

@router.delete("/{blocked_id}", dependencies=[Depends(get_current_admin)])
def delete_blocked(blocked_id: int, session: Session = Depends(get_session)):
    b = session.get(BlockedDate, blocked_id)
    if not b: raise HTTPException(404, "Not found")
    session.delete(b); session.commit()
    return {"deleted": blocked_id}