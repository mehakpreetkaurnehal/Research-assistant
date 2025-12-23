# # Dec 16, 2025
# import pdfplumber
# import csv
# import os

# def extract_pdfplumber(pdf_path, base):
#     text_all = []

#     with pdfplumber.open(pdf_path) as pdf:
#         for page_num, page in enumerate(pdf.pages, start=1):
#             # Text
#             text = page.extract_text()
#             if text:
#                 text_all.append(f"--- PAGE {page_num} ---")
#                 text_all.append(text)

#             # Tables
#             tables = page.extract_tables()
#             if tables:
#                 table_dir = f"{base}_tables"
#                 os.makedirs(table_dir, exist_ok=True)

#                 for idx, t in enumerate(tables, start=1):
#                     csv_path = os.path.join(table_dir, f"table_{page_num}_{idx}.csv")
#                     with open(csv_path, "w", newline="", encoding="utf-8") as f:
#                         writer = csv.writer(f)
#                         for r in t:
#                             writer.writerow([cell or "" for cell in r])
#                     print(f"Saved table: {csv_path}")

#     # Save text
#     with open(f"{base}_clean.txt", "w", encoding="utf-8") as f:
#         f.write("\n\n".join(text_all))

#     print("Text saved:", f"{base}_clean.txt")


# if __name__ == "__main__":
#     pdf_file = r"D:\Project\research_assistant\data\raw\pdfs\2511.15316v1.pdf"
#     base_out = r"D:\Project\research_assistant\16_dec_2511.15316v1"
#     extract_pdfplumber(pdf_file, base_out)





import requests
import os
import xml.etree.ElementTree as ET
import csv

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTChar, LTAnno, LTTextLine

###############################
# CONFIG — Change if needed
###############################

PDF_URL = "https://arxiv.org/pdf/2511.15316v1.pdf"
PDF_FILE = "paper.pdf"
XML_FILE = "paper.xml"   # we’ll generate this
TEXT_OUT = "paper_clean_text.txt"
TABLE_DIR = "paper_tables_xml"


###############################
# STEP 1 — Download PDF
###############################
def download_pdf(url, out_path):
    print(f"Downloading PDF from:\n  {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)
    print(f"✔ PDF downloaded -> {out_path}")


###############################
# STEP 2 — Create XML in memory
###############################
def create_xml_from_pdf(pdf_path, xml_path):
    print("\nCreating XML from PDF pages ...")

    # write root
    root = ET.Element("pdf")

    for page_layout in extract_pages(pdf_path):
        page_elem = ET.SubElement(root, "page")
        # collect text
        for obj in page_layout:
            if isinstance(obj, LTTextBoxHorizontal):
                for line in obj:
                    if isinstance(line, LTTextLine):
                        # create textline
                        line_elem = ET.SubElement(page_elem, "textline")
                        bbox = line.bbox
                        line_elem.set("bbox", f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}")
                        text = ""
                        for char in line:
                            if isinstance(char, LTAnno):
                                text += char.get_text()
                            elif isinstance(char, LTChar):
                                text += char.get_text()
                        ET.SubElement(line_elem, "text").text = text.strip()

    tree = ET.ElementTree(root)
    tree.write(xml_path, encoding="utf-8")
    print(f"✔ XML created -> {xml_path}")


###############################
# STEP 3 — Extract clean text
###############################
def extract_text(xml_path, text_out):
    print("\nExtracting clean text from XML ...")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    with open(text_out, "w", encoding="utf-8") as f:
        for p_idx, page in enumerate(root.findall("page"), start=1):
            f.write(f"=== PAGE {p_idx} ===\n")
            lines = []
            for tl in page.findall("textline"):
                bbox = tl.get("bbox")
                if bbox:
                    y0 = float(bbox.split(",")[1])
                    x0 = float(bbox.split(",")[0])
                    text = tl.find("text").text or ""
                    if text.strip():
                        lines.append((y0, x0, text))
            # sort by y desc, x asc
            lines.sort(key=lambda x: (-x[0], x[1]))
            for _, _, txt in lines:
                f.write(txt + "\n")
            f.write("\n")

    print(f"✔ Clean text saved -> {text_out}")


###############################
# STEP 4 — Extract tables
###############################
def extract_tables(xml_path, out_dir):
    print("\nExtracting tables ...")

    os.makedirs(out_dir, exist_ok=True)
    tree = ET.parse(xml_path)
    root = tree.getroot()

    table_count = 0

    for p_idx, page in enumerate(root.findall("page"), start=1):
        # group textlines by approximate y
        row_map = {}
        for tl in page.findall("textline"):
            bbox = tl.get("bbox")
            if not bbox:
                continue
            y0 = float(bbox.split(",")[1])
            x0 = float(bbox.split(",")[0])
            text = tl.find("text").text or ""
            if text.strip():
                key = round(y0, -1)
                row_map.setdefault(key, []).append((x0, text.strip()))

        # candidate rows with multiple columns
        table_rows = []
        for y_key, cells in row_map.items():
            if len(cells) > 1:
                sorted_cells = [txt for _, txt in sorted(cells, key=lambda c: c[0])]
                table_rows.append((y_key, sorted_cells))

        if table_rows:
            table_count += 1
            csv_path = os.path.join(out_dir, f"table_{table_count}_page{p_idx}.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # sort rows top->bottom
                for _, row in sorted(table_rows, key=lambda x: -x[0]):
                    writer.writerow(row)
            print(f"✔ Table {table_count} → {csv_path}")

    print(f"\n✔ Total Tables Extracted: {table_count}")


###############################
# RUN PIPELINE
###############################
if __name__ == "__main__":
    download_pdf(PDF_URL, PDF_FILE)
    create_xml_from_pdf(PDF_FILE, XML_FILE)
    extract_text(XML_FILE, TEXT_OUT)
    extract_tables(XML_FILE, TABLE_DIR)

    print("\n=== Extraction Completed Successfully! ===")
