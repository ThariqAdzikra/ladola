# pyrefly: ignore [missing-import]
import google.generativeai as genai
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

print(f"SDK Version: {genai.__version__}")

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: No API key found")
    exit(1)

genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("Model initialized")
    
    # Test system instruction support
    try:
        model_with_sys = genai.GenerativeModel(
            "gemini-3.1-flash-lite", 
            system_instruction="You are a helpful assistant."
        )
        print("System instruction supported")
    except TypeError as e:
        print(f"System instruction NOT supported: {e}")
    except Exception as e:
        print(f"Error testing system instruction: {e}")

    response = model.generate_content("Hello")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Gemini Test Failed: {e}")
