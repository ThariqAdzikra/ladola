import os
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker, declarative_base
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

# Load DATABASE_URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to a dummy URL or raise a clearer error to avoid 'None' type issues in IDE
    DATABASE_URL = "postgresql://user:pass@localhost/dbname" 
    print("[warn] DATABASE_URL not found in .env file! Using dummy fallback.")

# Engine SQLAlchemy untuk koneksi ke Neon Postgres
engine = create_engine(
    str(DATABASE_URL),
    pool_pre_ping=True, 
    pool_size=5,
    max_overflow=10
)

# Session local untuk digunakan di setiap request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk model SQLAlchemy
Base = declarative_base()

def get_db():
    """Dependency FastAPI untuk mendapatkan session database."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
