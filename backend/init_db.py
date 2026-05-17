import os
import sys
from pathlib import Path

# Add the current directory to sys.path to import local modules
sys.path.append(str(Path(__file__).parent))

from database import engine
from models import Base

def init_db():
    print("--- ChilliGuard Database Initialization ---")
    print(f"Connecting to: {engine.url.host}")
    
    try:
        print("Creating all tables in Neon Serverless...")
        Base.metadata.create_all(bind=engine)
        print("Success! Tables created: users, scans, chat_sessions, messages.")
    except Exception as e:
        print(f"Error during initialization: {e}")

if __name__ == "__main__":
    init_db()
