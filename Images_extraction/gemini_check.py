import os
from dotenv import load_dotenv
from pathlib import Path
from google import genai
from google.genai import types

# Load .env from parent folder
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)

# img_path = r'D:\Project\research_assistant\Images_extraction\data_imgdesc\images\page13_img0.png'
# img_path = r'D:\Project\research_assistant\Images_extraction\data_imgdesc\images\page7_img0.png'
img_path = r'C:\Users\hp\Downloads\download (1).png'
with open(img_path, 'rb') as f:
    image_bytes = f.read()

# Ask Gemini for 2–3 short paragraphs
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[
        types.Part.from_bytes(data=image_bytes, mime_type='image/png'),
        "Summarize this image in 2–3 short paragraphs covering all important information clearly and completely."
    ]
)

try:
    print(response.text or response.candidates[0].content.parts[0].text)
except:
    print(response)
