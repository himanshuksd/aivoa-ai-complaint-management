"""
database.py
------------
Sets up the SQLAlchemy engine + session. Defaults to a local SQLite file so
the project runs with zero setup for the demo. Swap DATABASE_URL in .env to
a postgres:// or mysql:// URL for a real deployment - no other code changes
needed because we only ever talk to SQLAlchemy's ORM layer.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./complaints.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency - yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
