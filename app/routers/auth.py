from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.database import get_session
from app.models import Admin
from app.security import verify_password, create_access_token
from app.schemas import Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(),
          session: Session = Depends(get_session)):
    admin = session.exec(select(Admin).where(Admin.email == form.username)).first()
    if not admin or not verify_password(form.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Bad credentials")
    return Token(access_token=create_access_token(admin.email))