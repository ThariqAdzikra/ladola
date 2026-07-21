import os
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, text
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv


# Load .env
load_dotenv("./backend/.env")
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL not found")
    exit(1)

# Ensure pooling is used if possible (neon)
if "pooler" not in DATABASE_URL and "neon.tech" in DATABASE_URL:
    print("Warning: Not using pooler URL")

engine = create_engine(DATABASE_URL)

migration_sql = """
ALTER TABLE messages ADD COLUMN IF NOT EXISTS scan_id INTEGER REFERENCES scans(id) ON DELETE SET NULL;
"""

try:
    with engine.connect() as conn:
        conn.execute(text(migration_sql))
        conn.commit()
        print("Migration successful: scan_id added to messages table.")
except Exception as e:
    print(f"Migration failed: {e}")
