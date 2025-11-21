# generation/generate.py

from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY is None:
    raise ValueError("Missing GEMINI_API_KEY env var")

# Instantiate Gemini client
client = genai.Client(api_key=API_KEY)

def llm_generate(prompt: str, model: str = "gemini-2.0-flash") -> str:
    """
    Generate an answer for the given prompt using Gemini API.
    """
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        # temperature=temperature,
        # max_tokens=max_tokens
    )
    # response may have structure depending on SDK version
    return response.text








# import os
# from dotenv import load_dotenv
# from openai import OpenAI, OpenAIError

# # Load environment variables from .env file
# load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")
# print("loaded openai_api key: ", api_key)
# # Read API key from environment variable

# if not api_key:
#     raise ValueError("Missing OPENAI_API_KEY environment variable. Please set it in your .env file.")

# # Instantiate the OpenAI client
# client = OpenAI(api_key=api_key)

# def llm_generate(
#     prompt: str,
#     # model: str = "gpt-3.5-turbo-0125",
#     model : str = "gpt-4o-mini", 
#     max_tokens: int = 100,
#     temperature: float = 0.2
# ) -> str:
#     """
#     Generate an answer for the given prompt using OpenAI API (v1.x interface).
#     :param prompt: The ful5l prompt string including context + question.
#     :param model: The model name to use.
#     :param max_tokens: Maximum tokens to generate.
#     :param temperature: Sampling temperature.
#     :return: Generated answer as a string.
#     """
#     try:
#         # Make chat completion request
#         response = client.chat.completions.create(
#             model=model,
#             messages=[
#                 {"role": "system", "content": "You are a helpful research assistant."},
#                 {"role": "user", "content": prompt}
#             ],
#             max_tokens=max_tokens,
#             temperature=temperature
#         )
#         # Extract the generated content
#         answer = response.choices[0].message.content
#         return answer

#     except OpenAIError as e:
#         # Handle API errors gracefully
#         print("OpenAI API error:", e)
#         raise

# # Example usage (uncomment for local testing)
# # if __name__ == "__main__":
# #     test_prompt = "What is machine learning?"
# #     print("Answer:", llm_generate(test_prompt))
