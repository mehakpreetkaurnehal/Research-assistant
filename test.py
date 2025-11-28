# import faiss
# index = faiss.read_index("data/storage/faiss_index.bin")
# print(index.ntotal)
# import sqlite3, json

# conn = sqlite3.connect("data/storage/metadata_full.db")
# cur = conn.cursor()
# cur.execute("SELECT COUNT(*) FROM chunks")
# print("Chunks:", cur.fetchone())
# conn.close()

# test for models 
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

MODELS = [
    "gemini-2.0-flash", "gemini-2.0-flash-lite-001",
    "gemini-2.5-flash"
]

def test_model(model_name):
    print(f"\n=== Testing model: {model_name} ===")
    try:
        config = types.GenerateContentConfig(
            max_output_tokens=50,
            temperature=0.1
        )
        response = client.models.generate_content(
            model=model_name,
            contents=f"Test: Say 'Hello from {model_name}'",
            config=config
        )
        print("SUCCESS:", response.text.strip())
    except Exception as e:
        print("FAILED:", e)

if __name__ == "__main__":
    for m in MODELS:
        test_model(m)



print("===Model Names===")
from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for m in client.models.list():
    print(m.name)
