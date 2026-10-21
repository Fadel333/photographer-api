from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.config import settings
from app.models import Admin
from app.security import hash_password
from app.routers import auth, packages, bookings, webhooks, availability


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as s:
        if not s.exec(select(Admin).where(Admin.email == settings.admin_email)).first():
            s.add(Admin(
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
            ))
            s.commit()
    yield


app = FastAPI(title="Photographer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.20.10.5:3000",
        "http://172.20.10.1:3000",
        "https://photographer-web-omega.vercel.app",   # ✅ Vercel production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(packages.router)
app.include_router(bookings.router)
app.include_router(webhooks.router)
app.include_router(availability.router)