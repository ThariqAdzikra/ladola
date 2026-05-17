import os
# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv(r"D:\ChilliGuard\backend\.env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Halo, tes koneksi."
    )
    print(response.text)
except Exception as e:
    print("Error with new SDK:", e)
