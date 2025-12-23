# import gradio as gr
# import os
# import json
# import base64
# import re
# from dotenv import load_dotenv
# from mistralai import Mistral

# # Load .env
# load_dotenv()
# api_key = os.environ.get("MISTRAL_API_KEY")
# print("Loaded key:", api_key)

# # Initialize client
# client = Mistral(api_key=api_key)

# # OCR function
# def extract_text_from_image(image_path):
#     with open(image_path, "rb") as f:
#         image_data = base64.b64encode(f.read()).decode()
    
#     response = client.chat.complete(
#         model="pixtral-12b-2409",
#         messages=[{
#             "role": "user",
#             "content": [
#                 {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_data}"},
#                 {"type": "text", "text": "Extract all text from this prescription, preserving structure and layout."}
#             ]
#         }]
#     )
#     return response.choices[0].message.content

# # ICD-10 extraction model
# def extract_icd10_codes(prescription_text):
#     system_prompt = """You are a medical coding expert. Extract ICD-10 codes from prescription text.

# RULES:
# - Identify all diagnoses, conditions, symptoms
# - If no ICD-10 code, return empty diagnoses
# - Map diagnoses to ICD-10 if possible
# - Return ONLY valid JSON

# OUTPUT FORMAT:
# {
#   "diagnoses": [
#     {
#       "condition": "condition name",
#       "icd10_code": "A00.0",
#       "description": "ICD-10 description",
#       "confidence": "low/medium/high",
#       "evidence": "text from prescription"
#     }
#   ],
#   "medications": ["list of meds mentioned"],
#   "notes": "any concerns"
# }"""

#     # Call the large model
#     response = client.chat.complete(
#         model="mistral-large-latest",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": f"Extract ICD-10 codes from this text:\n\n{prescription_text}"}
#         ],
#         response_format={"type": "json_object"}
#     )
    
#     return json.loads(response.choices[0].message.content)

# # Validate ICD-10 code format
# def validate_icd10_format(code):
#     pattern = r'^[A-Z]\d{2}(\.\d{1,4})?$'
#     return bool(re.match(pattern, code))

# # Main pipeline for Gradio
# def process_image(image_filepath):

#     # ===== Step 1: OCR =====
#     try:
#         extracted_text = extract_text_from_image(image_filepath)
#     except Exception as e:
#         return "", f"OCR failed: {str(e)}"

#     # ===== Step 2: ICD-10 Extraction =====
#     try:
#         icd10_data = extract_icd10_codes(extracted_text)
#     except Exception as e:
#         return extracted_text, f"ICD-10 extraction failed: {str(e)}"

#     # Check if ICD-10 block is empty
#     diagnoses = icd10_data.get("diagnoses", [])
#     if not diagnoses:
#         summary = "No ICD-10 codes found in the prescription text."
#         return extracted_text, summary

#     # Validate each code format
#     for diag in diagnoses:
#         code = diag.get("icd10_code", "")
#         diag["valid_format"] = validate_icd10_format(code)

#     pretty_json = json.dumps(icd10_data, indent=2)
#     return extracted_text, pretty_json

# # Gradio UI
# with gr.Blocks() as demo:
#     gr.Markdown("# 📄 Prescription OCR + ICD-10 Code Extraction")
    
#     with gr.Row():
#         image_input = gr.Image(type="filepath", label="Upload Prescription Image")
    
#     with gr.Row():
#         text_output = gr.Textbox(label="Extracted Text", lines=10)
#         result_output = gr.Code(label="ICD-10 Extraction Result", language="json")

#     image_input.change(process_image, image_input, [text_output, result_output])

# demo.launch()




import gradio as gr
import os
import json
import base64
import re
from dotenv import load_dotenv
from mistralai import Mistral

# Load .env
load_dotenv()
api_key = os.environ.get("MISTRAL_API_KEY")
print("Loaded key:", api_key)

client = Mistral(api_key=api_key)

def extract_text_from_image(image_path):
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    response = client.chat.complete(
        model="pixtral-12b-2409",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_data}"},
                {"type": "text", "text": "Extract all text from this prescription, preserving structure and layout."}
            ]
        }]
    )
    return response.choices[0].message.content

def extract_icd10_codes(prescription_text):
    system_prompt = """You are a medical coding expert. Extract ICD-10 codes from prescription text.

RULES:
- Identify all diagnoses, conditions, symptoms
- If no ICD-10 code, return empty diagnoses
- Map diagnoses to ICD-10 if possible
- Return ONLY valid JSON

OUTPUT FORMAT:
{
  "diagnoses": [
    {
      "condition": "condition name",
      "icd10_code": "A00.0",
      "description": "ICD-10 description",
      "confidence": "low/medium/high",
      "evidence": "text from prescription"
    }
  ],
  "medications": ["list of meds mentioned"],
  "notes": "any concerns"
}"""
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract ICD-10 codes from this text:\n\n{prescription_text}"}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def validate_icd10_format(code):
    pattern = r'^[A-Z]\d{2}(\.\d{1,4})?$'
    return bool(re.match(pattern, code))

def process_image(image_filepath):
    try:
        extracted_text = extract_text_from_image(image_filepath)
    except Exception as e:
        return "", f"❌ OCR failed: {str(e)}"

    try:
        icd10_data = extract_icd10_codes(extracted_text)
    except Exception as e:
        return extracted_text, f"❌ ICD-10 extraction failed: {str(e)}"

    diagnoses = icd10_data.get("diagnoses", [])
    if not diagnoses:
        return extracted_text, "✔ No ICD-10 codes found in the text."

    for diag in diagnoses:
        diag["valid_format"] = validate_icd10_format(diag.get("icd10_code", ""))

    pretty_json = json.dumps(icd10_data, indent=2)
    return extracted_text, pretty_json

# Gradio UI
with gr.Blocks(css="""
#title {text-align: center; font-size: 28px; font-weight: bold;}
#desc {text-align: center; margin-bottom: 20px; color: #555;}
.gradio-container {background-color: #f8f9fa;}
""") as demo:

    gr.HTML("<div id='title'>📄 Prescription OCR + ICD-10 Code Extractor</div>")
    gr.HTML("<div id='desc'>Upload a prescription image below — we will extract text and find ICD-10 codes if present.</div>")

    with gr.Row():
        with gr.Column(scale=1):
            image_input = gr.Image(type="filepath", label="📷 Upload Prescription Image")
            run_button = gr.Button("🔎 Process Image", variant="primary")
        with gr.Column(scale=1):
            text_output = gr.Textbox(label="📋 Extracted Text", lines=10)
            result_output = gr.Code(label="🧾 ICD-10 Extraction Result", language="json")

    run_button.click(process_image, image_input, [text_output, result_output])

demo.launch()
