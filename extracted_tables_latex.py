# December 18, 2025
# code is working well: extracted text, added in multiple files in .tex form
# multiple folders and files are created, 
# text file: paper_text_clean.txt



# import requests
# import tarfile
# import os
# import re
# from pathlib import Path

# def download_tex_source(arxiv_id, save_dir="./latex_sources"):
#     os.makedirs(save_dir, exist_ok=True)
#     url = f"https://arxiv.org/e-print/{arxiv_id}"
#     r = requests.get(url)
#     r.raise_for_status()
#     tar_path = os.path.join(save_dir, f"{arxiv_id}.tar.gz")
#     with open(tar_path, "wb") as f:
#         f.write(r.content)
#     print(f"✔ LaTeX source downloaded: {tar_path}")
#     return tar_path

# def extract_tar_gz(tar_path, extract_dir):
#     with tarfile.open(tar_path, "r:gz") as tar:
#         tar.extractall(path=extract_dir)
#     print(f"✔ Extracted LaTeX source to: {extract_dir}")

# def find_tex_files(root_dir):
#     tex_files = []
#     for root, _, files in os.walk(root_dir):
#         for file in files:
#             if file.endswith(".tex"):
#                 tex_files.append(os.path.join(root, file))
#     return tex_files

# def clean_latex_text(latex):
#     # Remove comments
#     no_comments = re.sub(r"%.*", "", latex)
#     # Remove LaTeX commands
#     no_commands = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", no_comments)
#     # Remove math (inline $...$ and display $$...$$)
#     no_math = re.sub(r"\$+.*?\$+", " ", no_commands)
#     # Collapse whitespace
#     cleaned = re.sub(r"\s+", " ", no_math)
#     return cleaned.strip()

# def extract_and_save_text(arxiv_id, output_file="extracted_text.txt"):
#     # Step 1: download source
#     tar_path = download_tex_source(arxiv_id)
#     extract_path = f"./latex_{arxiv_id}"
#     extract_tar_gz(tar_path, extract_path)

#     # Step 2: find and read all .tex files
#     tex_files = find_tex_files(extract_path)
#     print(f"Found {len(tex_files)} .tex files.")

#     all_text = []
#     for tex_file in tex_files:
#         with open(tex_file, "r", encoding="utf-8", errors="ignore") as f:
#             content = f.read()
#         cleaned = clean_latex_text(content)
#         all_text.append(cleaned)

#     combined_text = "\n\n".join(all_text)

#     # Step 3: save to one file
#     with open(output_file, "w", encoding="utf-8") as f:
#         f.write(combined_text)
#     print(f"✔ Clean text saved to {output_file}")

#     return output_file

# if __name__ == "__main__":
#     arxiv_id = "2511.15316v1"
#     extract_and_save_text(arxiv_id, "paper_text_clean.txt")




#2: same as above
# import os
# import re
# import requests
# import tarfile
# from pathlib import Path

# def download_arxiv_tex(arxiv_id, dest="recent_latex_sources"):
#     """Download the LaTeX source for a single arXiv ID"""
#     os.makedirs(dest, exist_ok=True)
#     url = f"https://arxiv.org/e-print/{arxiv_id}"
#     r = requests.get(url)
#     r.raise_for_status()
#     out_file = os.path.join(dest, f"{arxiv_id}.tar.gz")
#     with open(out_file, "wb") as f:
#         f.write(r.content)
#     print(f"✔ LaTeX source downloaded: {out_file}")
#     return out_file

# def extract_archive(tar_path, extract_to):
#     """Extract the LaTeX .tar.gz source"""
#     with tarfile.open(tar_path, "r:gz") as tar:
#         tar.extractall(path=extract_to)
#     print(f"✔ Extracted to {extract_to}")

# def clean_latex_text(text):
#     """
#     Remove LaTeX commands, math, and comments,
#     leaving human-readable text.
#     """
#     # remove LaTeX comments
#     text = re.sub(r"%.*", " ", text)
#     # remove math ($…$ and $$…$$)
#     text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.DOTALL)
#     text = re.sub(r"\$.*?\$", " ", text)
#     # remove LaTeX commands such as \command{…}
#     text = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", text)
#     # remove environment begins/ends
#     text = re.sub(r"\\(begin|end)\{.*?\}", " ", text)
#     # collapse whitespace
#     text = re.sub(r"\s+", " ", text)
#     return text.strip()

# def combine_and_clean_tex(folder):
#     """
#     Read all .tex files under the folder and produce
#     one combined clean text string.
#     """
#     combined = []
#     for root, _, files in os.walk(folder):
#         for file in sorted(files):
#             if file.endswith(".tex"):
#                 with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
#                     raw = f.read()
#                 cleaned = clean_latex_text(raw)
#                 combined.append(cleaned)

#     # join all cleaned pieces
#     return "\n\n".join(combined)

# def save_clean_text(arxiv_id, text, out_dir="recent_clean_texts"):
#     """Save the final cleaned text to a single .txt file"""
#     os.makedirs(out_dir, exist_ok=True)
#     out_file = os.path.join(out_dir, f"{arxiv_id}.txt")
#     with open(out_file, "w", encoding="utf-8") as f:
#         f.write(text)
#     print(f"✔ Clean text saved → {out_file}")
#     return out_file

# def process_one_paper(arxiv_id):
#     print(f"\n=== Processing {arxiv_id} ===")

#     # Download & extract LaTeX source
#     tar_path = download_arxiv_tex(arxiv_id)
#     extract_dir = f"./recent_latex_{arxiv_id}"
#     extract_archive(tar_path, extract_dir)

#     # Combine and clean all .tex files
#     combined_text = combine_and_clean_tex(extract_dir)

#     # Save to a single .txt file
#     return save_clean_text(arxiv_id, combined_text)

# if __name__ == "__main__":
#     # ⭐ Change this to test a single paper
#     arxiv_id = "2511.15316v1"
#     process_one_paper(arxiv_id)



#3 code is working well: saving tables in the .json format, but didn't mention the table_id in this.
# Saved: 2511.15316v1_clean_txt.txt
# Saved: 2511.15316v1_tables.json
import os
import re
import requests
import tarfile
import json
from pathlib import Path

def download_arxiv_tex(arxiv_id, dest="ltx_sources"):
    os.makedirs(dest, exist_ok=True)
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    r = requests.get(url)
    r.raise_for_status()
    out_file = os.path.join(dest, f"{arxiv_id}.tar.gz")
    with open(out_file, "wb") as f:
        f.write(r.content)
    return out_file

def extract_archive(tar_path, extract_to):
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=extract_to)

def find_tex_files(folder):
    tex_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".tex"):
                tex_files.append(os.path.join(root, file))
    return tex_files

def extract_tables_from_tex(tex):
    """
    Extract LaTeX tables from a string.
    Returns a list of tables as lists of rows.
    """
    tables = []
    for match in re.finditer(r"\\begin\{tabular\}(.*?)\\end\{tabular\}", tex, flags=re.DOTALL):
        content = match.group(1)
        # remove line breaks from multi-line formatting
        content = content.strip()
        # split rows on \\ that are not escaped
        raw_rows = re.split(r"\\\\", content)
        structured = []
        for raw_row in raw_rows:
            # split row into columns on unescaped &
            cols = [c.strip() for c in raw_row.split("&")]
            if len(cols) > 1:
                structured.append(cols)
        if structured:
            tables.append(structured)
    return tables

def clean_latex_text_except_tables(text):
    # remove comments
    text = re.sub(r"%.*", " ", text)
    # remove math
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.DOTALL)
    text = re.sub(r"\$.*?\$", " ", text)
    # replace table environments with placeholder so text stays logical
    text = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", " ", text, flags=re.DOTALL)
    # remove LaTeX commands
    text = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", text)
    # collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def process_arxiv_tex(arxiv_id):
    # step 1: download and extract
    tar_path = download_arxiv_tex(arxiv_id)
    extract_dir = f"./ltx_{arxiv_id}"
    extract_archive(tar_path, extract_dir)

    # find all .tex files
    tex_files = find_tex_files(extract_dir)

    all_clean_text = []
    all_tables = []

    for file in tex_files:
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # extract tables
        tables = extract_tables_from_tex(content)
        for t in tables:
            all_tables.append(t)

        # clean remaining text
        clean_text = clean_latex_text_except_tables(content)
        all_clean_text.append(clean_text)

    # combine text
    combined_text = "\n\n".join(all_clean_text)

    # save clean text
    text_out = f"{arxiv_id}_clean_txt.txt"
    with open(text_out, "w", encoding="utf-8") as f:
        f.write(combined_text)

    # save tables as JSON/CSV
    tables_out = f"{arxiv_id}_tables.json"
    with open(tables_out, "w", encoding="utf-8") as f:
        json_tables = {"tables": all_tables}
        json.dump(json_tables, f, indent=2)

    print(f"Saved: {text_out}")
    print(f"Saved: {tables_out}")
    return text_out, tables_out

if __name__ == "__main__":
    process_arxiv_tex("2511.15316v1")


