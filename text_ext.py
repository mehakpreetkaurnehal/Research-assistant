#problem with this approach: extracting text but it's not working properly as extracting text from left to right which is not making sense as the sequence of the data is mismatched.
# import logging
# import pdfplumber
# from pathlib import Path

# logging.getLogger("pdfminer").setLevel(logging.ERROR)

# pdf_path = Path(r"D:\Project\research_assistant\data\raw\pdfs\2511.15316v1.pdf")
# out_path = Path(r"D:\Project\research_assistant\2511.15316v1.txt")

# out_path.parent.mkdir(parents=True, exist_ok=True)

# with pdfplumber.open(pdf_path) as pdf:
#     text = ""
#     for page in pdf.pages:
#         page_text = page.extract_text()
#         if page_text:
#             text += page_text + "\n"

# out_path.write_text(text, encoding="utf-8")

# print(f"Saved to: {out_path}")


#approach 2
# Problem: again mismatch of the sequence

# import fitz          # PyMuPDF for text extraction
# import camelot      # Camelot for table extraction

# def extract_text(pdf_path):
#     """
#     Opens the PDF and extracts text in reading order.
#     fitz (PyMuPDF) returns "blocks" of text with coordinates.
#     Sorting by y (top→down) and x (left→right) approximates reading order.
#     """
#     doc = fitz.open(pdf_path)
#     all_text = ""

#     for page in doc:
#         blocks = page.get_text("blocks")
#         blocks.sort(key=lambda b: (b[1], b[0]))
        
#         for block in blocks:
#             text = block[4].strip()
#             if text:
#                 all_text += text + "\n"

#     return all_text

# def extract_tables(pdf_path):
#     """
#     Camelot tries to detect tables on given pages.
#     'stream' mode works when tables don't have explicit borders,
#     but are aligned in columns.
#     """
#     tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
#     table_outputs = []

#     for i, table in enumerate(tables):
#         df = table.df
#         table_outputs.append(f"--- TABLE {i+1} ---\n{df.to_string(index=False)}\n")

#     return "\n".join(table_outputs)

# if __name__ == "__main__":
#     # Path to the PDF
#     pdf_path = r"D:\Project\research_assistant\data\raw\pdfs\2511.15316v1.pdf"

#     # Extract text
#     print("Extracting text from PDF...")
#     extracted_text = extract_text(pdf_path)

#     # Extract tables
#     print("Extracting tables from PDF...")
#     extracted_tables = extract_tables(pdf_path)

#     # Combine text and tables into one output
#     full_output = (
#         "===== EXTRACTED TEXT =====\n\n"
#         + extracted_text
#         + "\n\n===== EXTRACTED TABLES =====\n\n"
#         + extracted_tables
#     )

#     # Save to .txt file
#     out_file = r"D:\Project\research_assistant\2511.15316v1_extracted.txt"
#     with open(out_file, "w", encoding="utf-8") as f:
#         f.write(full_output)

#     print(f"Extraction saved to: {out_file}")



#better but issue is not completely extracting text, missing some important information
# import fitz  # PyMuPDF
# import os
# import re

# CAPTION_PATTERN = re.compile(r"^(Figure|Fig\.|Table)\s*\d+", re.IGNORECASE)

# def extract_clean_text(pdf_path):
#     doc = fitz.open(pdf_path)
#     final_text = []

#     for page in doc:
#         page_width = page.rect.width
#         mid_x = page_width / 2

#         blocks = page.get_text("dict")["blocks"]

#         # 1️⃣ Detect image regions
#         image_bboxes = [
#             b["bbox"] for b in blocks if b["type"] == 1
#         ]

#         def overlaps_image(text_bbox):
#             for img in image_bboxes:
#                 if (
#                     text_bbox[0] < img[2]
#                     and text_bbox[2] > img[0]
#                     and text_bbox[1] < img[3]
#                     and text_bbox[3] > img[1]
#                 ):
#                     return True
#             return False

#         # 2️⃣ Filter valid text blocks
#         text_blocks = []
#         for b in blocks:
#             if b["type"] != 0:
#                 continue
#             if overlaps_image(b["bbox"]):
#                 continue
#             text_blocks.append(b)

#         # 3️⃣ Split into columns
#         left_col = []
#         right_col = []

#         for b in text_blocks:
#             x0 = b["bbox"][0]
#             if x0 < mid_x:
#                 left_col.append(b)
#             else:
#                 right_col.append(b)

#         # 4️⃣ Sort blocks top → bottom
#         left_col.sort(key=lambda b: b["bbox"][1])
#         right_col.sort(key=lambda b: b["bbox"][1])

#         ordered_blocks = left_col + right_col

#         # 5️⃣ Extract text + remove captions
#         for block in ordered_blocks:
#             block_lines = []
#             for line in block["lines"]:
#                 line_text = " ".join(span["text"] for span in line["spans"]).strip()
#                 if not line_text:
#                     continue
#                 if CAPTION_PATTERN.match(line_text):
#                     continue
#                 block_lines.append(line_text)

#             if not block_lines:
#                 continue

#             paragraph = " ".join(block_lines)

#             # 6️⃣ Paragraph cleanup
#             paragraph = re.sub(r"\s+", " ", paragraph).strip()

#             if paragraph:
#                 final_text.append(paragraph)

#     return "\n\n".join(final_text)


# if __name__ == "__main__":
#     pdf_file = r"D:\Project\research_assistant\data\raw\pdfs\2511.15316v1.pdf"
#     output_txt = r"D:\Project\research_assistant\recent_2511.15316v1_clean.txt"

#     os.makedirs(os.path.dirname(output_txt), exist_ok=True)

#     text = extract_clean_text(pdf_file)

#     with open(output_txt, "w", encoding="utf-8") as f:
#         f.write(text)

#     print(f"✅ Clean extraction saved to:\n{output_txt}")



# import camelot

# # Extract tables from the PDF
# tables = camelot.read_pdf( r"D:\Project\research_assistant\data\raw\pdfs\2511.15316v1.pdf", flavor = 'stream')

# # Print the number of tables extracted
# print(f"Number of tables extracted: {len(tables)}")

# # Print the first table
# # print(tables[0].df)
# print(tables[0].df.iloc[37])

import pdfplumber
import csv
import os

def extract_tables(pdf_path, output_base):
    with pdfplumber.open(pdf_path) as pdf:

        table_counter = 1
        for page_num, page in enumerate(pdf.pages, start=1):

            # Extract tables
            tables = page.extract_tables()

            if not tables:
                continue

            for table in tables:
                # Check if the table has at least 2 rows and multiple columns
                if len(table) < 2 or all(len(row) < 2 for row in table):
                    continue

                # Build CSV path
                out_dir = f"{output_base}_tables"
                os.makedirs(out_dir, exist_ok=True)
                csv_path = os.path.join(out_dir,
                                        f"table_{table_counter}_page{page_num}.csv")

                # Save table as CSV
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    for row in table:
                        writer.writerow([cell or "" for cell in row])

                print(f"✔ Saved: {csv_path}")
                table_counter += 1

    print(f"\nExtraction complete. {table_counter-1} table(s) saved.")

if __name__ == "__main__":
    pdf_file = r"D:\Project\research_assistant\data\raw\pdfs\2511.15316v1.pdf"
    output_base = r"D:\Project\research_assistant\pdf_plumber_2511.15316v1"
    extract_tables(pdf_file, output_base)

# import pdfplumber
# import re
# import os

# # Patterns to detect captions
# CAPTION_PATTERN = re.compile(r"^(Figure|Fig\.?|Table)\s*\d+[:.]?", re.IGNORECASE)

# def valid_table(table):
#     # skip junk: must have at least 2 rows and 2+ columns
#     if not table or len(table) < 2:
#         return False
#     col_counts = {len(r) for r in table}
#     return (len(col_counts) == 1 and list(col_counts)[0] >= 2)

# def extract_pdf(pdf_path):
#     text_paragraphs = []
#     tables = []

#     with pdfplumber.open(pdf_path) as pdf:
#         for pnum, page in enumerate(pdf.pages, start=1):

#             # ---- 1️⃣ Extract tables ----
#             raw_tables = page.extract_tables()
#             for t in raw_tables:
#                 if valid_table(t):
#                     tables.append((pnum, t))

#             # ---- 2️⃣ Extract text words ----
#             words = page.extract_words(use_text_flow=True)

#             # ---- 3️⃣ Column separation ----
#             mid = page.width / 2
#             left = []
#             right = []
#             for w in sorted(words, key=lambda x: (x["top"], x["x0"])):
#                 if w["x0"] < mid:
#                     left.append(w)
#                 else:
#                     right.append(w)

#             # ---- 4️⃣ Combine into paragraphs ----
#             def words_to_paragraphs(word_list):
#                 paras, current, last_y, last_x = [], "", None, None
#                 for w in word_list:
#                     y, x0, x1 = w["top"], w["x0"], w["x1"]
#                     if last_y and abs(y - last_y) > 8:
#                         if current.strip():
#                             paras.append(current.strip())
#                         current = w["text"]
#                     else:
#                         if last_x and (x0 - last_x) > 5:
#                             current += " " + w["text"]
#                         else:
#                             current += w["text"]
#                     last_y, last_x = y, x1
#                 if current.strip():
#                     paras.append(current.strip())
#                 return paras

#             text_paragraphs.extend(words_to_paragraphs(left))
#             text_paragraphs.extend(words_to_paragraphs(right))

#     return text_paragraphs, tables

# def save_output(texts, tables, base):
#     # save clean text
#     txt_file = f"{base}_clean.txt"
#     with open(txt_file, "w", encoding="utf-8") as f:
#         for para in texts:
#             if CAPTION_PATTERN.match(para):
#                 continue
#             f.write(para + "\n\n")

#     print(f"Text saved to: {txt_file}")

#     # save structured tables
#     tabdir = f"{base}_tables"
#     os.makedirs(tabdir, exist_ok=True)

#     for i, (pnum, table) in enumerate(tables, start=1):
#         out_csv = os.path.join(tabdir, f"table_{i}_page{pnum}.csv")
#         with open(out_csv, "w", encoding="utf-8") as f:
#             for row in table:
#                 safe_row = [str(cell).replace(",", ";") if cell else "" for cell in row]
#                 f.write(",".join(safe_row) + "\n")

#     print(f"{len(tables)} tables saved under: {tabdir}")

# if __name__ == "__main__":
#     pdf_file = r"D:\Project\research_assistant\data\raw\pdfs\2511.15316v1.pdf"
#     base = r"D:\Project\research_assistant\2511.15316v1"
#     txt, tbls = extract_pdf(pdf_file)
#     save_output(txt, tbls, base)
