#16 12 25, afternoon

import pymupdf4llm
import pathlib
from pymupdf4llm import LlamaMarkdownReader

pdf_path = r"D:\Project\research_assistant\data\raw\pdfs\2511.15316v1.pdf"

# to_markdown() converts all the pages to a combined Markdown text
# It handles headers, tables, lists, bold/italic/codes, images, and more
try:
    md_text = pymupdf4llm.to_markdown(pdf_path)
except Exception as e:
    print("Error processing PDF:", e)
    raise

# Save Markdown output as a .md file
output_md_path = pathlib.Path("research_output.md")
output_md_path.write_text(md_text, encoding="utf-8")
print(f"✔ Markdown saved to {output_md_path}")

# Setting page_chunks=True produces a list of dicts per page
page_data = pymupdf4llm.to_markdown(pdf_path, page_chunks=True, write_images=True,
                                     image_path="extracted_images")

# page_data is now a list of dictionaries, one per page
# Each dict contains:
# - metadata: PDF metadata like title/author/page count
# - toc_items: table of contents items
# - tables: any detected tables on the page
# - images: list of images extracted
# - graphics: detected vector graphics
# - text: the page text in Markdown
print("Structured page data extracted.")

for i, page in enumerate(page_data[:3]):
    print(f"\n--- Page {i} Text Preview ---\n", page["text"][:350])

try:
    llama_reader = LlamaMarkdownReader()
    # load_data returns a list of objects compatible with LlamaIndex
    llama_docs = llama_reader.load_data(pdf_path)
    print(f"✔ Loaded {len(llama_docs)} documents for LlamaIndex")
except Exception as e:
    print("Could not build LlamaIndex docs:", e)

print("\nDone! Your PDF is now:")
print(f"- Markdown exported: {output_md_path}")
print("- Structured page list ready in `page_data`")
print("- Images (if detected) in ./extracted_images/")
