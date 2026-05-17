import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(r"D:\ChilliGuard\backend\.env")

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print(f"Testing with API key: {api_key[:5]}...")

model_name = "gemini-flash-latest"
gemini_model = genai.GenerativeModel(model_name)

gemini_history = [
    {"role": "user", "parts": ["Halo, saya butuh bantuan dengan tanaman cabai saya."]},
    {"role": "model", "parts": ["Halo, saya asisten ChilliGuard. Dari foto terakhir terdeteksi Bercak Daun."]}
]

print("Starting chat session...")
try:
    chat_session = gemini_model.start_chat(history=gemini_history)
    print("Chat session started successfully.")
    
    prompt = "Bagaimana cara mengobatinya?"
    print(f"Sending prompt: {prompt}")
    
    response = chat_session.send_message(prompt)
    print("Response received:")
    print(response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
