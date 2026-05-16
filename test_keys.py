import os
from dotenv import load_dotenv
import requests
import google.generativeai as genai

load_dotenv('backend/.env')

print("Testing OWM...")
owm_key = os.getenv("OPENWEATHER_KEY")
res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q=Islamabad,PK&appid={owm_key}&units=metric")
print(res.status_code)
print(res.json())

print("Testing Gemini...")
genai.configure(api_key=os.getenv("GEMINI_KEY"))
try:
    models = [m.name for m in genai.list_models()]
    print("Models:", models)
    print("Has gemini-2.0-flash:", 'models/gemini-2.0-flash' in models or 'models/gemini-2.0-flash-exp' in models)
except Exception as e:
    print("Gemini error:", e)
