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
# from google import genai
# from google.genai import types
# import os
# from dotenv import load_dotenv

# load_dotenv()
# API_KEY = os.getenv("GEMINI_API_KEY")

# client = genai.Client(api_key=API_KEY)

# MODELS = [
#     "gemini-2.0-flash", "gemini-2.0-flash-lite-001",
#     "gemini-2.5-flash"
# ]

# def test_model(model_name):
#     print(f"\n=== Testing model: {model_name} ===")
#     try:
#         config = types.GenerateContentConfig(
#             max_output_tokens=50,
#             temperature=0.1
#         )
#         response = client.models.generate_content(
#             model=model_name,
#             contents=f"Test: Say 'Hello from {model_name}'",
#             config=config
#         )
#         print("SUCCESS:", response.text.strip())
#     except Exception as e:
#         print("FAILED:", e)

# if __name__ == "__main__":
#     for m in MODELS:
#         test_model(m)



# print("===Model Names===")
# from google import genai
# import os

# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# for m in client.models.list():
#     print(m.name)


#test whether API key and HF_TOKEN are working
# import os
# from dotenv import load_dotenv

# load_dotenv()  
# print("GEMINI_API_KEY:", os.getenv("GEMINI_API_KEY"))
# print("HF_TOKEN:", os.getenv("HF_TOKEN"))


# testing model for HF_TOKEN and API_KEY
# from generation.generate import llm_generate

# prompt = "Explain the concept of machine learning in simple words."

# print("🔍 Sending test prompt...")
# answer = llm_generate(prompt)

# print("\nFinal Answer:\n", answer)



# from generation.generate import llm_generate

# query = "What is machine learning? Explain in simple terms."

# print(llm_generate(query))


import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

# A FREE model that works with router API
HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

client = InferenceClient(model=HF_MODEL, token=HF_TOKEN)

prompt = "Explain deep learning in one paragraph."

print("\n=== Testing Hugging Face Model ===\n")

response = client.chat.completions.create(
    model=HF_MODEL,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=200,
)

print("\nMODEL RESPONSE:\n")
print(response.choices[0].message["content"])
