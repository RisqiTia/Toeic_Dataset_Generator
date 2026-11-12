from google import genai

GEMINI_API_KEY = "AIzaSyBA81deOfb-0-x-GcZ9uIiUSc9KEoG8tFs" #API
PEXELS_API_KEY = "gHXNyUNJy7RxX1kVOLlPXtPjbV5I3WJTjmXMWMOcpfyWCO9RhlQQCNRg"

client = genai.Client(api_key=GEMINI_API_KEY)

LEVELS = ["Beginner", "Intermediate", "Advanced"]

TOTAL_QUESTIONS = 10
TOTAL_BATCH = 1 # ubah kalau mau generate berkali-kali dalam 1 run
DELAY_BETWEEN_QUESTION = 1
DELAY_BETWEEN_LEVEL = 60