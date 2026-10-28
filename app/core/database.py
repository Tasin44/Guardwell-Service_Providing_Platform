

from threading import settrace_all_threads
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker,Session
from app.core.config import settings



# Engine setup: Connect args for SQLite to allow multiple threads in dev mode
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}


engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Optimization: Verifies connection liveliness before executing queries
)

# Session factory for generating db sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for all SQLAlchemy models (Analogous to django.db.models.Model)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency generator for Database Sessions.
    Yields an active database session and ensures it is safely closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
