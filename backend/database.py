import os
from typing import Optional
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker, declarative_base
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# pyrefly: ignore [missing-import]
from fastapi import HTTPException

try:
    # pyrefly: ignore [missing-import]
    from sqlalchemy.engine import make_url
except Exception:  # pragma: no cover
    make_url = None  # type: ignore[assignment]

load_dotenv()

# Load DATABASE_URL from .env or environment
DATABASE_URL = os.getenv("DATABASE_URL")
APP_ENV = os.getenv("APP_ENV", "development")

engine_error: Optional[str] = None
database_url_safe: Optional[str] = None

def _safe_url(value: str) -> str:
    if make_url is not None:
        try:
            return make_url(value).render_as_string(hide_password=True)
        except Exception:
            return "<invalid DATABASE_URL>"
    # Fallback: don't risk leaking secrets
    return "<DATABASE_URL set>"

if not DATABASE_URL:
    if APP_ENV == "production":
        engine_error = "DATABASE_URL is not set in production environment"
        print("[critical] DATABASE_URL is not set in production environment!")
    else:
        # Local development fallback to SQLite if Postgres is not available
        DATABASE_URL = "sqlite:///./chilliguard.db"
        print(f"[warn] DATABASE_URL not found. Falling back to {DATABASE_URL} for {APP_ENV}.")

# Engine SQLAlchemy
# Use connect_args={"check_same_thread": False} only for SQLite
engine_args = {
    "pool_pre_ping": True,
}

if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args.update({
        "pool_size": 5,
        "max_overflow": 10
    })

engine = None
SessionLocal = None

if DATABASE_URL:
    database_url_safe = _safe_url(DATABASE_URL)
    if database_url_safe == "<invalid DATABASE_URL>":
        engine_error = "DATABASE_URL is malformed (could not be parsed)"
        print("[critical] DATABASE_URL is malformed. Check username/password encoding and include @host/dbname.")
    else:
        try:
            engine = create_engine(str(DATABASE_URL), **engine_args)
            # Session local
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        except Exception as exc:  # pragma: no cover
            engine_error = f"{type(exc).__name__} while initializing database engine"
            print("[critical] Failed to initialize database engine:", type(exc).__name__)

if SessionLocal is None:
    print("[warn] Database is not ready; endpoints that require DB will return 503.")

# Base class for models
Base = declarative_base()

def get_db():
    """FastAPI dependency to get database session."""
    if SessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DB_NOT_READY",
                "message": "Database is not configured or failed to initialize.",
                "database_url": database_url_safe,
                "error": engine_error,
            },
        )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
