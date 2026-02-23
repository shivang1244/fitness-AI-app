from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Temporary: using SQLite for initial setup
DATABASE_URL = "sqlite:///./fitness_ai.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed only for SQLite
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
