import os
import re
import requests
import tarfile
import json

def download_arxiv_tex(arxiv_id, dest="tID_latex_sources"):
    print(f"→ Downloading LaTeX source for {arxiv_id} ...")
    os.makedirs(dest, exist_ok=True)
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    r = requests.get(url)
    if r.status_code != 200:
        print(f"❌ Failed to download LaTeX source (status {r.status_code})")
        return None
    out_file = os.path.join(dest, f"{arxiv_id}.tar.gz")
    with open(out_file, "wb") as f:
        f.write(r.content)
    print(f"✔ Downloaded LaTeX source: {out_file}")
    return out_file

def extract_archive(tar_path, extract_to):
    if not tar_path:
        return False
    print(f"→ Extracting archive to {extract_to} ...")
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=extract_to)
        print("✔ Extraction complete")
        return True
    except Exception as e:
        print("❌ Extraction failed:", e)
        return False

def find_tex_files(folder):
    print("→ Searching for .tex files ...")
    tex_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".tex"):
                tex_files.append(os.path.join(root, file))
    print(f"✔ Found {len(tex_files)} .tex files")
    return tex_files

def extract_tables_and_marker_text(tex_text, table_counter_start=1):
    tables = []
    counter = table_counter_start

    def table_replacer(match):
        nonlocal counter
        content = match.group(1).strip()
        raw_rows = re.split(r"\\\\", content)
        structured = []
        for raw in raw_rows:
            row = [c.strip() for c in raw.split("&")]
            if len(row) > 1:
                structured.append(row)
        if structured:
            table_id = f"Table_{counter}"
            tables.append({"table_id": table_id, "rows": structured})
            marker = f"\n<<{table_id}>>\n"
            counter += 1
            return marker
        return ""

    cleaned_text = re.sub(
        r"\\begin\{tabular\}(.*?)\\end\{tabular\}",
        table_replacer, tex_text, flags=re.DOTALL
    )
    return cleaned_text, tables, counter

def clean_latex_text(text):
    text = re.sub(r"%.*", " ", text)
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.DOTALL)
    text = re.sub(r"\$.*?\$", " ", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", text)
    text = re.sub(r"\\(begin|end)\{.*?\}", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def process_arxiv_with_table_markers(arxiv_id):
    tar_path = download_arxiv_tex(arxiv_id)

    if not tar_path:
        print("🚫 No LaTeX source available — cannot proceed")
        return

    extract_dir = f"./tID_latex_{arxiv_id}"
    if not extract_archive(tar_path, extract_dir):
        print("🚫 Extraction failed — stopping")
        return

    tex_files = find_tex_files(extract_dir)
    if not tex_files:
        print("🚫 No .tex files found — stopping")
        return

    table_counter = 1
    all_tables = []
    all_marker_text = []

    for file in sorted(tex_files):
        print(f"→ Processing {file}")
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        text_with_markers, tables, table_counter = extract_tables_and_marker_text(content, table_counter)
        all_tables.extend(tables)

        cleaned = clean_latex_text(text_with_markers)
        all_marker_text.append(cleaned)

    combined_text = "\n\n".join(all_marker_text)

    # Save outputs
    text_out = f"{arxiv_id}_text_with_table_markers.txt"
    with open(text_out, "w", encoding="utf-8") as f:
        f.write(combined_text)
    print(f"✔ Combined text with markers saved as: {text_out}")

    tables_out = f"{arxiv_id}_tables_ID.json"
    with open(tables_out, "w", encoding="utf-8") as f:
        json.dump({"tables": all_tables}, f, indent=2)
    print(f"✔ Tables saved as: {tables_out}")

    print("✅ Done processing")

if __name__ == "__main__":
    # Change the ID here
    process_arxiv_with_table_markers("2511.15316v1")
