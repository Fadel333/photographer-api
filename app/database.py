from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # Checks if connection is alive before using it
    pool_recycle=300,     # Recycles connections every 5 minutes
)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)