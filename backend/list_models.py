import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(r"D:\ChilliGuard\backend\.env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print("Error listing models:", e)
