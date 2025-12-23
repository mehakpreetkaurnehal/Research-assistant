# output: my_papers in different form 
# import arxiv
# import os

# def download_arxiv_paper(arxiv_id, output_dir="./my_papers"):
#     os.makedirs(output_dir, exist_ok=True)

#     search = arxiv.Search(id_list=[arxiv_id])
#     paper = next(search.results())

#     pdf_file = paper.download_pdf(dirpath=output_dir)
#     print(f"Downloaded: {pdf_file}")
#     print("Title:", paper.title)
#     print("Authors:", paper.authors)

#     return pdf_file

# if __name__ == "__main__":
#     download_arxiv_paper("2511.15316")
# print("DONE!")

#17
# import arxiv
# import os
# import pymupdf4llm
# import camelot
# import pandas as pd
# import pathlib
# import warnings

# # Suppress PyMuPDF non-fatal warnings
# warnings.filterwarnings("ignore", "Cannot set gray non-stroke color")

# # --- STEP 1: download arXiv paper ---
# def download_arxiv_paper(arxiv_id, output_dir="./papers"):
#     os.makedirs(output_dir, exist_ok=True)
#     # using the new Client API
#     client = arxiv.Client()
#     search = client.results(arxiv.Search(id_list=[arxiv_id]))
#     paper = next(search)
#     pdf_path = paper.download_pdf(dirpath=output_dir)
#     print(f"Downloaded PDF to: {pdf_path}")
#     print("Title:", paper.title)
#     print("Authors:", paper.authors)
#     return pdf_path

# # --- STEP 2: extract text as Markdown ---
# def extract_markdown(pdf_path, md_path="paper_output.md"):
#     md_text = pymupdf4llm.to_markdown(pdf_path)
#     pathlib.Path(md_path).write_text(md_text, encoding="utf-8")
#     print(f"Text extracted → {md_path}")
#     return md_path

# # --- STEP 3: extract tables with Camelot ---
# def extract_tables(pdf_path, output_dir="tables_output"):
#     os.makedirs(output_dir, exist_ok=True)

#     # try lattice mode first (better for grid tables)
#     tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
#     print(f"Lattice mode detected {tables.n} tables")

#     # if none found, try stream mode
#     if tables.n == 0:
#         print("No tables with lattice → switching to stream mode")
#         tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")

#     csv_files = []
#     for i, table in enumerate(tables):
#         csv_path = os.path.join(output_dir, f"table_{i+1}.csv")
#         table.df.to_csv(csv_path, index=False)
#         csv_files.append(csv_path)
#         print(f"Saved table_{i+1} → {csv_path}")

#     return csv_files

# # --- RUN ALL TOGETHER ---
# if __name__ == "__main__":
#     pdf_file = download_arxiv_paper("2511.15316")
#     md_file = extract_markdown(pdf_file)
#     csvs = extract_tables(pdf_file)

#     print("\nExtraction complete!")
#     print("Markdown file:", md_file)
#     print("Tables:", csvs)



#Approach 2:
# import arxiv
# import os
# import requests
# import pdfplumber
# import camelot
# import json

# GROBID_URL = "http://localhost:8070/api/processFulltextDocument"

# def download_arxiv_pdf(arxiv_id, save_dir="./my_research_papers"):
#     os.makedirs(save_dir, exist_ok=True)
#     search = arxiv.Search(id_list=[arxiv_id])
#     results = list(search.results())
#     if not results:
#         raise ValueError(f"No arXiv paper found for {arxiv_id}")
#     paper = results[0]
#     pdf_path = paper.download_pdf(dirpath=save_dir)
#     return pdf_path

# def parse_with_grobid(pdf_path):
#     with open(pdf_path, "rb") as f:
#         files = {"input": f}
#         r = requests.post(GROBID_URL, files=files)
#         r.raise_for_status()
#         return r.text

# def extract_tables(pdf_path):
#     tables = []
#     for flavor in ["lattice", "stream"]:
#         try:
#             tables += camelot.read_pdf(pdf_path, pages="all", flavor=flavor).docs
#         except Exception:
#             pass

#     structured = []
#     for i, t in enumerate(tables):
#         df = t.df
#         cols = df.iloc[0].tolist()
#         rows = df.iloc[1:].values.tolist()
#         structured.append({
#             "table_id": f"Table_{i+1}",
#             "caption": "",
#             "columns": cols,
#             "rows": rows
#         })
#     return structured

# def extract_text_chunks(pdf_path):
#     chunks = []
#     with pdfplumber.open(pdf_path) as pdf:
#         for page_num, page in enumerate(pdf.pages):
#             text = (page.extract_text() or "").strip()
#             if text:
#                 chunks.append({
#                     "chunk_type": "section_text",
#                     "page_number": page_num + 1,
#                     "text": text
#                 })
#     return chunks

# def process_arxiv_paper(arxiv_id, output_dir="./my_research_papers"):
#     os.makedirs(output_dir, exist_ok=True)

#     pdf_path = download_arxiv_pdf(arxiv_id, output_dir)

#     xml = parse_with_grobid(pdf_path)
#     xml_file = os.path.join(output_dir, f"{arxiv_id}.xml")
#     with open(xml_file, "w") as f:
#         f.write(xml)

#     text_chunks = extract_text_chunks(pdf_path)
#     table_structs = extract_tables(pdf_path)

#     output = {
#         "arxiv_id": arxiv_id,
#         "pdf_path": pdf_path,
#         "xml_path": xml_file,
#         "chunks": text_chunks,
#         "tables": table_structs
#     }

#     out_json = os.path.join(output_dir, f"{arxiv_id}_structured.json")
#     with open(out_json, "w") as f:
#         json.dump(output, f, indent=2)

#     print(f"Structured output saved at → {out_json}")
#     return output

# if __name__ == "__main__":
#     arxiv_id = "2301.00001"
#     process_arxiv_paper(arxiv_id)




#17 afernoon: need to check once, as output was somewhat correct, but need to check once again

# import urllib.parse
# import urllib.request
# import xml.etree.ElementTree as ET
# import requests
# import fitz  # PyMuPDF
# import os

# def fetch_arxiv_metadata(arxiv_id):
#     """
#     Fetch metadata (title, authors, abstract, PDF link) from the arXiv API XML.
#     """
#     base_url = "http://export.arxiv.org/api/query?"
#     params = {
#         "id_list": arxiv_id,
#     }
#     url = base_url + urllib.parse.urlencode(params)
#     with urllib.request.urlopen(url) as response:
#         xml_data = response.read().decode("utf-8")
    
#     root = ET.fromstring(xml_data)
#     ns = {"atom": "http://www.w3.org/2005/Atom"}
#     entry = root.find("atom:entry", ns)
#     if entry is None:
#         raise ValueError("No entry found in arXiv API response")
    
#     metadata = {}
#     metadata["title"] = entry.find("atom:title", ns).text.strip()
#     metadata["abstract"] = entry.find("atom:summary", ns).text.strip()
#     metadata["authors"] = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
    
#     # Extract the PDF link
#     for link in entry.findall("atom:link", ns):
#         if link.attrib.get("type") == "application/pdf":
#             metadata["pdf_url"] = link.attrib["href"]
#             break
    
#     return metadata

# def download_pdf(url, save_path):
#     """
#     Download PDF from a URL to a local file path.
#     """
#     r = requests.get(url)
#     r.raise_for_status()
#     with open(save_path, "wb") as f:
#         f.write(r.content)
#     print(f"Downloaded PDF: {save_path}")
#     return save_path

# def extract_text_from_pdf(pdf_path):
#     """
#     Extract full text from the PDF using PyMuPDF (fitz).
#     """
#     text = []
#     doc = fitz.open(pdf_path)
#     for page in doc:
#         text.append(page.get_text())
#     return "\n".join(text)

# if __name__ == "__main__":
#     arxiv_id = "2511.15316"  # Example
#     metadata = fetch_arxiv_metadata(arxiv_id)
#     print("Title:", metadata["title"])
#     print("Authors:", metadata["authors"])
#     print("Abstract:", metadata["abstract"])
    
#     # Download the PDF
#     pdf_filename = f"{arxiv_id}.pdf"
#     pdf_path = download_pdf(metadata["pdf_url"], pdf_filename)
    
#     # Extract text
#     full_text = extract_text_from_pdf(pdf_path)
#     print("\n===== Extracted Full Text Preview =====\n")
#     print(full_text[:30000])

