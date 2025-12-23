# import os
# from mistralai import Mistral
# import json
# import base64
# import re

# # Initialize client
# from dotenv import load_dotenv

# # Load environment variables from .env
# load_dotenv()  
# # Get the key
# api_key = os.environ.get("MISTRAL_API_KEY")
# print(api_key)


# client = Mistral(api_key=api_key)

# # Step 1: OCR - Extract text from prescription image
# def extract_text_from_image(image_path):
#     with open(image_path, "rb") as f:
#         image_data = base64.b64encode(f.read()).decode()
    
#     response = client.chat.complete(
#         model="mistral-ocr-latest",
#         messages=[{
#             "role": "user",
#             "content": [
#                 {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_data}"},
#                 {"type": "text", "text": "Extract all text from this prescription, preserving structure and layout."}
#             ]
#         }]
#     )
#     return response.choices[0].message.content

# # Step 2: Extract ICD-10 codes from text
# def extract_icd10_codes(prescription_text):
#     system_prompt = """You are a medical coding expert. Extract ICD-10 codes from prescription text.

# RULES:
# - Identify all diagnoses, conditions, symptoms
# - Map to specific ICD-10 codes
# - Include code, description, confidence level
# - Return ONLY valid JSON

# OUTPUT FORMAT:
# {
#   "diagnoses": [
#     {
#       "condition": "condition name",
#       "icd10_code": "A00.0",
#       "description": "ICD-10 description",
#       "confidence": "high/medium/low",
#       "evidence": "text from prescription"
#     }
#   ],
#   "medications": ["list of meds mentioned"],
#   "requires_review": true/false,
#   "notes": "any concerns"
# }"""

#     response = client.chat.complete(
#         model="mistral-large-latest",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": f"Extract ICD-10 codes from this prescription:\n\n{prescription_text}"}
#         ],
#         response_format={"type": "json_object"}
#     )
    
#     return json.loads(response.choices[0].message.content)

# # Validate ICD-10 code format
# def validate_icd10_format(code):
#     pattern = r'^[A-Z]\d{2}(\.\d{1,4})?$'
#     return bool(re.match(pattern, code))

# # Main pipeline
# def process_prescription(image_path):
#     print("Step 1: Extracting text from image...")
#     extracted_text = extract_text_from_image(image_path)
#     print(f"Extracted Text:\n{extracted_text}\n")
    
#     print("Step 2: Extracting ICD-10 codes...")
#     icd10_data = extract_icd10_codes(extracted_text)
    
#     # Validate codes
#     for diagnosis in icd10_data.get('diagnoses', []):
#         code = diagnosis['icd10_code']
#         is_valid = validate_icd10_format(code)
#         diagnosis['format_valid'] = is_valid
#         if not is_valid:
#             print(f"⚠️  Invalid code format: {code}")
    
#     print("\nExtracted ICD-10 Codes:")
#     print(json.dumps(icd10_data, indent=2))
    
#     return icd10_data

# # Usage
# if __name__ == "__main__":
#     result = process_prescription("prescription.jpg")
    
#     # Save to file
#     with open("icd10_codes.json", "w") as f:
#         json.dump(result, f, indent=2)


#gradio
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

# Initialize client
client = Mistral(api_key=api_key)

# OCR function
def extract_text_from_image(image_path):
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    response = client.chat.complete(
        model="mistral-ocr-latest",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_data}"},
                {"type": "text", "text": "Extract all text from this prescription, preserving structure and layout."}
            ]
        }]
    )
    return response.choices[0].message.content

# ICD10 extraction
def extract_icd10_codes(prescription_text):
    system_prompt = """You are a medical coding expert. Extract ICD-10 codes from prescription text.

RULES:
- Identify all diagnoses, conditions, symptoms
- Map to specific ICD-10 codes
- Include code, description, confidence level
- Return ONLY valid JSON

OUTPUT FORMAT:
{
  "diagnoses": [
    {
      "condition": "condition name",
      "icd10_code": "A00.0",
      "description": "ICD-10 description",
      "confidence": "high/medium/low",
      "evidence": "text from prescription"
    }
  ],
  "medications": ["list of meds mentioned"],
  "requires_review": true/false,
  "notes": "any concerns"
}"""

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract ICD-10 codes from this prescription:\n\n{prescription_text}"}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# ICD10 format validator
def validate_icd10_format(code):
    pattern = r'^[A-Z]\d{2}(\.\d{1,4})?$'
    return bool(re.match(pattern, code))

# Main processing
def process_image(image):
    # Save uploaded image to disk
    image_path = image.name
    
    # Step 1: OCR
    extracted_text = extract_text_from_image(image_path)

    # Step 2: ICD10 extraction
    try:
        icd10_data = extract_icd10_codes(extracted_text)
    except Exception as e:
        icd10_data = {"error": str(e)}

    # Validate codes
    if "diagnoses" in icd10_data:
        for diag in icd10_data["diagnoses"]:
            code = diag.get("icd10_code", "")
            diag["format_valid"] = validate_icd10_format(code)

    # Create displayable output
    pretty_json = json.dumps(icd10_data, indent=2)

    return extracted_text, pretty_json

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# Prescription OCR + ICD‒10 Extraction")
    
    with gr.Row():
        image_input = gr.Image(type="filepath", label="Upload Prescription Image")
    
    with gr.Row():
        text_output = gr.Textbox(label="Extracted Text", lines=10)
        json_output = gr.Code(label="ICD-10 + Medications JSON", language="json")
    
    image_input.upload(process_image, image_input, [text_output, json_output])

demo.launch()
