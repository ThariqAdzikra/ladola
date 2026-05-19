import os
import sys
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker, declarative_base
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

# Load DATABASE_URL from .env or environment
DATABASE_URL = os.getenv("DATABASE_URL")
APP_ENV = os.getenv("APP_ENV", "development")

if not DATABASE_URL:
    if APP_ENV == "production":
        print("[critical] DATABASE_URL is not set in production environment!")
        sys.exit(1)
    else:
        # Local development fallback to SQLite if Postgres is not available
        DATABASE_URL = "sqlite:///./chilliguard.db"
        print(f"[warn] DATABASE_URL not found. Falling back to {DATABASE_URL} for {APP_ENV}.")

# Engine SQLAlchemy
# Use connect_args={"check_same_thread": False} only for SQLite
engine_args = {
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args.update({
        "pool_size": 5,
        "max_overflow": 10
    })

engine = create_engine(str(DATABASE_URL), **engine_args)

# Session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """FastAPI dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
