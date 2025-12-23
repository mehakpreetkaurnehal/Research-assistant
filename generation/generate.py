# generation/generate.py

# #code: hugging face fallback function added
# from google import genai
# from google.genai import types
# import os
# from dotenv import load_dotenv

# import sys
# sys.stdout.reconfigure(encoding='utf-8')
# sys.stderr.reconfigure(encoding='utf-8')

# load_dotenv()
# API_KEY = os.getenv("GEMINI_API_KEY")
# if API_KEY is None:
#     raise ValueError("Missing GEMINI_API_KEY environment variable. Please set it in your .env file.")

# # Initialize Gemini client
# client = genai.Client(api_key=API_KEY)

# # MODEL PRIORITY LIST (auto fallback)
# MODEL_CHAIN = [
#     "gemini-2.0-flash",
#     "gemini-2.0-flash-lite-001",
#     "gemini-2.5-flash"
# ]

# # HF ADDITION
# from huggingface_hub import InferenceClient
# HF_TOKEN = os.getenv("HF_TOKEN")   # Add HF token in .env
# HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

# hf_client = None
# if HF_TOKEN:
#     hf_client = InferenceClient(model=HF_MODEL, token=HF_TOKEN)


# def _try_generate(prompt, model, max_tokens, temperature):
#     """Try generating using a single Gemini model. Return text OR None."""
#     try:
#         config = types.GenerateContentConfig(
#             max_output_tokens=max_tokens,
#             temperature=temperature,
#         )
#         response = client.models.generate_content(
#             model=model,
#             contents=prompt,
#             config=config
#         )
#         if response and response.text:
#             return response.text.strip()

#     except Exception as e:
#         print(f"[LLM ERROR] Model '{model}' failed → {e}")

#     return None  # signal failure


# # HF FALLBACK FUNCTION
# def _hf_generate(prompt, max_tokens, temperature):
#     """Fallback: Try generating using Hugging Face LLM."""
#     if hf_client is None:
#         print("HF_TOKEN missing. Skipping HuggingFace fallback.")
#         return None

#     try:
#         print(f"Using HuggingFace fallback: {HF_MODEL}")
        
#         response = hf_client.text_generation(
#             prompt,
#             max_new_tokens=max_tokens,
#             temperature=temperature,
#             top_p=0.9
#         )
#         return response.strip()

#     except Exception as e:
#         print(f"❌ HF LLM failed → {e}")
#         return None


# def llm_generate(
#     prompt: str,
#     max_tokens: int = 1000,
#     temperature: float = 0.2
# ) -> str:
#     """
#     Generate an answer using Gemini models.
#     If ALL Gemini models fail, fallback to HuggingFace Mistral.
#     """

#     # Try Gemini chain
#     for model in MODEL_CHAIN:
#         print(f"🔎 Trying Gemini model: {model}")
#         result = _try_generate(prompt, model, max_tokens, temperature)

#         if result:
#             print(f"✅ Gemini model succeeded: {model}")
#             return result

#         print(f"Gemini model failed, trying next...")

#     # ⭐ Try HF fallback
#     hf_result = _hf_generate(prompt, max_tokens, temperature)
#     if hf_result:
#         print("HuggingFace fallback succeeded.")
#         return hf_result

#     # If ALL fail:
#     print("ALL MODELS FAILED (Gemini + HuggingFace).")
#     return (
#         "I’m sorry, but I couldn’t generate a complete answer due to temporary "
#         "LLM issues. Please try again later."
#     )
    
    

#added code after adding different models
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY is None:
    raise ValueError("Missing GEMINI_API_KEY environment variable. Please set it in your .env file.")

# Initialize client once
client = genai.Client(api_key=API_KEY)

# MODEL PRIORITY LIST (auto fallback)
MODEL_CHAIN = [
    "gemini-2.0-flash",      # primary
    "gemini-2.0-flash-lite-001",
    "gemini-2.5-flash"
       
]


def _try_generate(prompt, model, max_tokens, temperature):
    """Try generating using a single model. Return text OR None."""
    try:
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )

        if response and response.text:
            return response.text.strip()

    except Exception as e:
        print(f"[LLM ERROR] Model '{model}' failed → {e}")

    return None  # signal failure


def llm_generate(
    prompt: str,
    max_tokens: int = 1000, # increase token length 
    temperature: float = 0.2
) -> str:
    """
    Generate an answer using Gemini API with fallback:
    1. gemini-2.0-flash
    2. gemini-2.0-flash-lite-001
    3. gemini-2.5-flash
    """

    for model in MODEL_CHAIN:
        print(f"🔎 Trying model: {model}")
        result = _try_generate(prompt, model, max_tokens, temperature)

        if result:
            print(f"✅ Model succeeded: {model}")
            return result

        print(f"⚠️ Model failed, switching to next...")

    # If ALL models fail:
    print("❌ ALL LLM MODELS FAILED.")
    return (
        "I’m sorry, but I couldn’t generate a complete answer due to temporary "
        "LLM issues. Please try again in a moment."
    )






# #right code for genai before adding fallback
# # from google import genai
# # from google.genai import types
# # import os
# # from dotenv import load_dotenv

# # import sys
# # sys.stdout.reconfigure(encoding='utf-8')
# # sys.stderr.reconfigure(encoding='utf-8')

# # load_dotenv()
# # API_KEY = os.getenv("GEMINI_API_KEY")
# # if API_KEY is None:
# #     raise ValueError("Missing GEMINI_API_KEY environment variable. Please set it in your .env file.")

# # client = genai.Client(api_key=API_KEY)

# # def llm_generate(
# #     prompt: str,
# #     model: str = "gemini-2.0-flash",
# #     max_tokens: int = 800, #512 earlier
# #     temperature: float = 0.2
# # ) -> str:
# #     """
# #     Generate an answer for the given prompt using Gemini API.
# #     The prompt is expected to include context from research papers only.
# #     """
# #     try:
# #         config = types.GenerateContentConfig(
# #             max_output_tokens=max_tokens,
# #             temperature=temperature
# #         )
# #         response = client.models.generate_content(
# #             model=model,
# #             contents=prompt,
# #             config = config
# #         )
# #         return response.text
# #     except Exception as e:
# #         print("Error during generation:", e)
# #         raise

















# right working code for genai
# from google import genai
# import os
# from dotenv import load_dotenv

# load_dotenv()
# API_KEY = os.getenv("GEMINI_API_KEY")
# if API_KEY is None:
#     raise ValueError("Missing GEMINI_API_KEY env var")

# # Instantiate Gemini client
# client = genai.Client(api_key=API_KEY)

# def llm_generate(prompt: str, model: str = "gemini-2.0-flash") -> str:
#     """
#     Generate an answer for the given prompt using Gemini API.
#     """
#     response = client.models.generate_content(
#         model=model,
#         contents=prompt,
#         # temperature=temperature,
#         # max_tokens=max_tokens
#     )
#     # response 
#     return response.text





