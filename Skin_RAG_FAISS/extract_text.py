# extracting the text 
# import os
# import re
# import sqlite3
# import requests
# import tarfile
# from Bio import Entrez
# import arxiv
# import fitz  # PyMuPDF
# from bs4 import BeautifulSoup

# # ==============================
# # CONFIGURATION (parameterized)
# # ==============================
# EMAIL = os.getenv("NCBI_EMAIL", "mehakpreetk1909@gmail.com")
# DB_PATH = os.getenv("EXTRACT_DB_PATH", "data/research_text.db")
# TEXT_OUT_DIR = os.getenv("EXTRACT_TEXT_OUT", "data/fulltexts")
# ARXIV_LATEX_DIR = os.getenv("ARXIV_LATEX_DIR", "data/arxiv_latex_src")
# PUBMED_MAX = int(os.getenv("PUBMED_MAX_RESULTS", "30"))
# ARXIV_MAX = int(os.getenv("ARXIV_MAX_RESULTS", "30"))

# os.makedirs(TEXT_OUT_DIR, exist_ok=True)
# os.makedirs(ARXIV_LATEX_DIR, exist_ok=True)

# Entrez.email = EMAIL

# # ==============================
# # DATABASE SETUP
# # ==============================
# conn = sqlite3.connect(DB_PATH)
# cur = conn.cursor()

# cur.execute("""
# CREATE TABLE IF NOT EXISTS papers_metadata (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     source TEXT,
#     paper_id TEXT,
#     pmcid TEXT,
#     doi TEXT,
#     title TEXT,
#     authors TEXT,
#     journal TEXT,
#     clickable_url TEXT,
#     abstract TEXT
# );
# """)

# cur.execute("""
# CREATE TABLE IF NOT EXISTS papers_fulltext (
#     metadata_id INTEGER,
#     full_text TEXT,
#     FOREIGN KEY(metadata_id) REFERENCES papers_metadata(id)
# );
# """)
# conn.commit()

# # ==============================
# # TEXT CLEANING UTILITY
# # ==============================
# def sanitize_text(text: str) -> str:
#     return re.sub(r"\s+", " ", text).strip()

# # ==============================
# # PUBMED + PMC EXTRACTION
# # ==============================
# def convert_to_pmcid(pmid: str) -> str:
#     """Convert PMID to PMCID via PMC idconv API."""
#     url = f"https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?ids={pmid}&format=json"
#     r = requests.get(url, timeout=10)
#     if r.status_code == 200:
#         try:
#             rec = r.json().get("records", [{}])[0]
#             return rec.get("pmcid", "")
#         except:
#             return ""
#     return ""

# def fetch_pubmed_fulltext(pmid: str):
#     """Fetch PubMed metadata + PMC full text if available."""
#     pmcid = convert_to_pmcid(pmid)
#     clickable_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

#     handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml")
#     xmlrec = Entrez.read(handle)["PubmedArticle"][0]
#     art = xmlrec["MedlineCitation"]["Article"]

#     title = art.get("ArticleTitle", "")
#     authors_list = []
#     for a in art.get("AuthorList", []):
#         last = a.get("LastName")
#         initials = a.get("Initials")
#         collective = a.get("CollectiveName")
#         if last and initials:
#             authors_list.append(f"{last} {initials}")
#         elif collective:
#             authors_list.append(collective)
#     authors = ", ".join(authors_list)

#     journal = art["Journal"]["Title"]
#     abstract = ""
#     if "Abstract" in art:
#         abstract = sanitize_text(" ".join(art["Abstract"]["AbstractText"]))

#     doi = ""
#     for aid in xmlrec["PubmedData"]["ArticleIdList"]:
#         if aid.attributes.get("IdType") == "doi":
#             doi = str(aid)

#     # Try PMC full text
#     full_text = ""
#     if pmcid:
#         try:
#             pmc_xml = Entrez.efetch(db="pmc", id=pmcid, retmode="xml", rettype="full").read().decode("utf-8")
#             pmc_xml = re.sub(r"<fig.*?</fig>", " ", pmc_xml, flags=re.DOTALL)

#             table_count = 1
#             def table_repl(match):
#                 nonlocal table_count
#                 content = sanitize_text(re.sub(r"<.*?>", " ", match.group(0)))
#                 marker = f"\n<<<TABLE_{table_count}>>>\n{content}\n"
#                 table_count += 1
#                 return marker

#             pmc_xml = re.sub(r"<table-wrap.*?</table-wrap>", table_repl, pmc_xml, flags=re.DOTALL)
#             full_text = sanitize_text(re.sub(r"<.*?>", " ", pmc_xml))
#         except:
#             full_text = ""

#     if not full_text:  # fallback to abstract only
#         full_text = abstract

#     # Store in SQLite
#     cur.execute("""
#     INSERT INTO papers_metadata(
#         source, paper_id, pmcid, doi, title, authors, journal, clickable_url, abstract
#     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """, ("pubmed", pmid, pmcid, doi, title, authors, journal, clickable_url, abstract))
#     conn.commit()
#     meta_id = cur.lastrowid

#     cur.execute("""
#     INSERT INTO papers_fulltext (metadata_id, full_text)
#     VALUES (?, ?)
#     """, (meta_id, full_text))
#     conn.commit()

#     # Write .txt output
#     out_file = os.path.join(TEXT_OUT_DIR, f"pubmed_{pmid}.txt")
#     with open(out_file, "w", encoding="utf-8") as f:
#         f.write(f"TITLE: {title}\nURL: {clickable_url}\nDOI: {doi}\nPMCID: {pmcid}\n\n")
#         f.write(full_text)

#     print("[PubMed] Saved:", out_file)

# # ==============================
# # arXiv EXTRACTION (HTML → LaTeX → PDF)
# # ==============================
# def fetch_arxiv_html(arxiv_id: str) -> str | None:
#     """Try HTML versions first (arxiv.org/html and ar5iv mirror)."""
#     urls = [
#         f"https://arxiv.org/html/{arxiv_id}",
#         f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
#     ]
#     for url in urls:
#         try:
#             r = requests.get(url, timeout=20)
#             if r.status_code == 200:
#                 soup = BeautifulSoup(r.text, "html.parser")
#                 return sanitize_text(soup.get_text(separator="\n"))
#         except:
#             continue
#     return None

# def download_arxiv_latex(arxiv_id: str) -> str | None:
#     """Download LaTeX source package."""
#     path = os.path.join(ARXIV_LATEX_DIR, f"{arxiv_id}.tar.gz")
#     url = f"https://arxiv.org/e-print/{arxiv_id}"
#     r = requests.get(url, timeout=30)
#     if r.status_code == 200:
#         with open(path, "wb") as f:
#             f.write(r.content)
#         return path
#     return None

# def extract_latex_dir(tar_path: str, arxiv_id: str) -> str | None:
#     """Extract LaTeX tarball."""
#     folder = os.path.join(ARXIV_LATEX_DIR, arxiv_id)
#     os.makedirs(folder, exist_ok=True)
#     try:
#         with tarfile.open(tar_path, "r:gz") as tar:
#             tar.extractall(path=folder)
#         return folder
#     except:
#         return None

# def clean_latex_text(txt: str) -> str:
#     """Remove LaTeX markup."""
#     txt = re.sub(r"%.*", " ", txt)
#     txt = re.sub(r"\$.*?\$", " ", txt)
#     txt = re.sub(r"\\begin\{.*?\}", " ", txt)
#     txt = re.sub(r"\\end\{.*?\}", " ", txt)
#     txt = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", txt)
#     return sanitize_text(txt)

# def extract_tables_from_tex(tex: str, count: int):
#     """Extract tabular environments with markers."""
#     tables = []
#     def repl(m):
#         nonlocal count
#         raw = m.group(1).strip()
#         rows = [sanitize_text(r) for r in raw.split("\\\\") if "&" in r]
#         marker = f"\n<<<TABLE_{count}>>>\n"
#         tables.append((marker, rows))
#         count += 1
#         return marker

#     new_tex = re.sub(r"\\begin\{tabular\}(.*?)\\end\{tabular\}", repl, tex, flags=re.DOTALL)
#     return new_tex, tables, count

# def process_arxiv_paper(arxiv_id: str):
#     """Fetch and extract full text from arXiv paper."""
#     clickable_url = f"https://arxiv.org/abs/{arxiv_id}"
#     result = next(arxiv.Search(query=f"id:{arxiv_id}", max_results=1).results(), None)
#     if not result:
#         print("[arXiv] Not found:", arxiv_id)
#         return

#     title = sanitize_text(result.title)
#     authors = ", ".join(str(a) for a in result.authors)
#     doi = result.doi or ""
#     journal_ref = result.journal_ref or ""

#     # Build text with basic info
#     full_text = (f"arXivID: {arxiv_id}\nURL: {clickable_url}\n"
#                  f"DOI: {doi}\nTitle: {title}\n\n")

#     # 1) Try HTML
#     html_text = fetch_arxiv_html(arxiv_id)
#     if html_text:
#         full_text += html_text
#     else:
#         # 2) Try LaTeX
#         latex_tar = download_arxiv_latex(arxiv_id)
#         if latex_tar:
#             folder = extract_latex_dir(latex_tar, arxiv_id)
#             if folder:
#                 table_counter = 1
#                 for root, _, files in os.walk(folder):
#                     for nm in files:
#                         if nm.endswith(".tex"):
#                             raw = open(os.path.join(root, nm), "r", encoding="utf-8", errors="ignore").read()
#                             raw, tbl, table_counter = extract_tables_from_tex(raw, table_counter)
#                             for marker, rows in tbl:
#                                 full_text += marker + "\n" + "\n".join(rows) + "\n"
#                             full_text += clean_latex_text(raw) + "\n"
#         else:
#             # 3) Fallback to PDF
#             pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
#             r = requests.get(pdf_url, timeout=20)
#             if r.status_code == 200:
#                 pdf_temp = os.path.join(ARXIV_LATEX_DIR, f"{arxiv_id}.pdf")
#                 with open(pdf_temp, "wb") as f:
#                     f.write(r.content)
#                 doc = fitz.open(pdf_temp)
#                 for page in doc:
#                     full_text += sanitize_text(page.get_text())

#     # Insert into DB
#     cur.execute("""
#     INSERT INTO papers_metadata(
#         source, paper_id, pmcid, doi, title, authors, journal, clickable_url, abstract
#     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """, ("arxiv", arxiv_id, "", doi, title, authors, journal_ref, clickable_url, "")) 
#     conn.commit()
#     meta_id = cur.lastrowid

#     cur.execute("""
#     INSERT INTO papers_fulltext (metadata_id, full_text)
#     VALUES (?, ?)
#     """, (meta_id, full_text))
#     conn.commit()

#     out_file = os.path.join(TEXT_OUT_DIR, f"arxiv_{arxiv_id}.txt")
#     with open(out_file, "w", encoding="utf-8") as f:
#         f.write(full_text)
#     print("[arXiv] Saved:", out_file)

# # ==============================
# # MAIN EXECUTION
# # ==============================
# def main():
#     KEYWORD = os.getenv("SEARCH_KEYWORD", "skin OR dermatology OR dermatitis")

#     # PubMed search
#     print("🔍 Searching PubMed...")
#     query = f"({KEYWORD}) AND (pubmed pmc open access[filter])"
#     pmids = Entrez.read(Entrez.esearch(db="pubmed", term=query, retmax=PUBMED_MAX))["IdList"]
#     for pmid in pmids:
#         fetch_pubmed_fulltext(pmid)

#     # arXiv search
#     print("🔍 Searching arXiv...")
#     arxiv_results = arxiv.Search(query=f"all:{KEYWORD}", max_results=ARXIV_MAX).results()
#     for r in arxiv_results:
#         aid = r.entry_id.split("/")[-1]
#         process_arxiv_paper(aid)

#     conn.close()
#     print("✅ Extraction complete!")

# if __name__ == "__main__":
#     main()


# this code need to test: arxiv is not working yet so, in this keywords are added related to skin related tasks.
import os
import re
import sqlite3
import requests
import tarfile
from Bio import Entrez
import arxiv
import fitz  # PyMuPDF
from bs4 import BeautifulSoup

# ==============================
# CONFIGURATION (parameterized)
# ==============================
# Load from environment or defaults
Entrez.email = os.getenv("NCBI_EMAIL", "")  #add email
DB_PATH = os.getenv("EXTRACT_DB_PATH", "data/research_text.db")
TEXT_OUT_DIR = os.getenv("EXTRACT_TEXT_OUT", "data/fulltexts")
ARXIV_LATEX_DIR = os.getenv("ARXIV_LATEX_DIR", "data/arxiv_latex_src")

PUBMED_MAX = int(os.getenv("PUBMED_MAX_RESULTS", "50"))
ARXIV_MAX = int(os.getenv("ARXIV_MAX_RESULTS", "50"))

# Parameterize keywords via environment
SEARCH_KEYWORDS = os.getenv(
    "SEARCH_KEYWORDS",
    "skin OR dermatology OR dermatitis OR eczema OR psoriasis OR melanoma"
)

os.makedirs(TEXT_OUT_DIR, exist_ok=True)
os.makedirs(ARXIV_LATEX_DIR, exist_ok=True)

# ==============================
# DATABASE SETUP
# ==============================
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS papers_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    paper_id TEXT,
    pmcid TEXT,
    doi TEXT,
    title TEXT,
    authors TEXT,
    journal TEXT,
    clickable_url TEXT,
    abstract TEXT
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS papers_fulltext (
    metadata_id INTEGER,
    full_text TEXT,
    FOREIGN KEY(metadata_id) REFERENCES papers_metadata(id)
);
""")

conn.commit()

# ==============================
# TEXT CLEANING UTILITY
# ==============================
def sanitize_text(text):
    return re.sub(r"\s+", " ", text).strip()

# ==============================
# PUBMED + PMC EXTRACTION
# ==============================
def convert_to_pmcid(pmid):
    url = f"https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?ids={pmid}&format=json"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        try:
            rec = r.json().get("records", [{}])[0]
            return rec.get("pmcid", "")
        except:
            return ""
    return ""

def fetch_pubmed_fulltext(pmid):
    pmcid = convert_to_pmcid(pmid)
    clickable_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml")
    xmlrec = Entrez.read(handle)["PubmedArticle"][0]
    art = xmlrec["MedlineCitation"]["Article"]

    title = art.get("ArticleTitle", "")
    authors_list = []
    for a in art.get("AuthorList", []):
        last = a.get("LastName")
        initials = a.get("Initials")
        collective = a.get("CollectiveName")
        if last and initials:
            authors_list.append(f"{last} {initials}")
        elif collective:
            authors_list.append(collective)
    authors = ", ".join(authors_list)
    journal = art["Journal"]["Title"]

    abstract = ""
    if "Abstract" in art:
        abstract = sanitize_text(" ".join(art["Abstract"]["AbstractText"]))

    doi = ""
    for aid in xmlrec["PubmedData"]["ArticleIdList"]:
        if aid.attributes.get("IdType") == "doi":
            doi = str(aid)

    full_text = ""
    if pmcid:
        try:
            pmc_xml = Entrez.efetch(db="pmc", id=pmcid, retmode="xml", rettype="full").read().decode("utf-8")
            pmc_xml = re.sub(r"<fig.*?</fig>", " ", pmc_xml, flags=re.DOTALL)

            table_count = 1
            def table_repl(m):
                nonlocal table_count
                content = sanitize_text(re.sub(r"<.*?>", " ", m.group(0)))
                marker = f"\n<<<TABLE_{table_count}>>>\n{content}\n"
                table_count += 1
                return marker

            pmc_xml = re.sub(r"<table-wrap.*?</table-wrap>", table_repl, pmc_xml, flags=re.DOTALL)
            full_text = sanitize_text(re.sub(r"<.*?>", " ", pmc_xml))
        except:
            full_text = ""

    if not full_text:
        full_text = abstract

    cur.execute("""
    INSERT INTO papers_metadata(
        source, paper_id, pmcid, doi, title, authors, journal, clickable_url, abstract
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("pubmed", pmid, pmcid, doi, title, authors, journal, clickable_url, abstract))
    conn.commit()
    meta_id = cur.lastrowid

    cur.execute("""INSERT INTO papers_fulltext (metadata_id, full_text) VALUES (?,?)""",
                (meta_id, full_text))
    conn.commit()

    out_file = os.path.join(TEXT_OUT_DIR, f"pubmed_{pmid}.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"TITLE: {title}\nURL: {clickable_url}\nDOI: {doi}\nPMCID: {pmcid}\n\n{full_text}")

    print("[PubMed] Saved:", out_file)

# ==============================
# arXiv EXTRACTION
# ==============================
def fetch_arxiv_html(arxiv_id):
    urls = [f"https://arxiv.org/html/{arxiv_id}", f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"]
    for url in urls:
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                return sanitize_text(soup.get_text(separator="\n"))
        except:
            continue
    return None

def download_arxiv_latex(arxiv_id):
    path = os.path.join(ARXIV_LATEX_DIR, f"{arxiv_id}.tar.gz")
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    r = requests.get(url, timeout=30)
    if r.status_code == 200:
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    return None

def extract_latex_dir(tar_path, arxiv_id):
    folder = os.path.join(ARXIV_LATEX_DIR, arxiv_id)
    os.makedirs(folder, exist_ok=True)
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=folder)
        return folder
    except:
        return None

def clean_latex_text(txt):
    txt = re.sub(r"%.*", " ", txt)
    txt = re.sub(r"\$.*?\$", " ", txt)
    txt = re.sub(r"\\begin\{.*?\}", " ", txt)
    txt = re.sub(r"\\end\{.*?\}", " ", txt)
    txt = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", txt)
    return sanitize_text(txt)

def extract_tables_from_tex(tex, count):
    tables = []
    def repl(m):
        nonlocal count
        raw = m.group(1).strip()
        rows = [sanitize_text(r) for r in raw.split("\\\\") if "&" in r]
        marker = f"\n<<<TABLE_{count}>>>\n"
        tables.append((marker, rows))
        count += 1
        return marker
    new_tex = re.sub(r"\\begin\{tabular\}(.*?)\\end\{tabular\}", repl, tex, flags=re.DOTALL)
    return new_tex, tables, count

def process_arxiv_paper(arxiv_id):
    clickable_url = f"https://arxiv.org/abs/{arxiv_id}"
    result = next(arxiv.Search(query=f"id:{arxiv_id}", max_results=1).results(), None)
    if not result:
        print("[arXiv] Not found:", arxiv_id)
        return

    title = sanitize_text(result.title)
    authors = ", ".join(str(a) for a in result.authors)
    doi = result.doi or ""
    journal_ref = result.journal_ref or ""
    full_text = f"arXivID: {arxiv_id}\nURL: {clickable_url}\nDOI: {doi}\nTitle: {title}\n\n"

    html_version = fetch_arxiv_html(arxiv_id)
    if html_version:
        full_text += html_version
    else:
        latex_tar = download_arxiv_latex(arxiv_id)
        if latex_tar:
            folder = extract_latex_dir(latex_tar, arxiv_id)
            table_counter = 1
            if folder:
                for root, _, files in os.walk(folder):
                    for nm in files:
                        if nm.endswith(".tex"):
                            raw = open(os.path.join(root, nm), "r", encoding="utf-8", errors="ignore").read()
                            raw, tbl, table_counter = extract_tables_from_tex(raw, table_counter)
                            for marker, rows in tbl:
                                full_text += marker + "\n" + "\n".join(rows) + "\n"
                            full_text += clean_latex_text(raw) + "\n"
        else:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            r = requests.get(pdf_url, timeout=20)
            if r.status_code == 200:
                pdf_temp = os.path.join(ARXIV_LATEX_DIR, f"{arxiv_id}.pdf")
                with open(pdf_temp, "wb") as f:
                    f.write(r.content)
                doc = fitz.open(pdf_temp)
                for page in doc:
                    full_text += sanitize_text(page.get_text())

    cur.execute("""
    INSERT INTO papers_metadata(
        source, paper_id, pmcid, doi, title, authors, journal, clickable_url, abstract
    ) VALUES (?,?,?,?,?,?,?,?,?)
    """, ("arxiv", arxiv_id, "", doi, title, authors, journal_ref, clickable_url, ""))
    conn.commit()
    meta_id = cur.lastrowid
    cur.execute("""INSERT INTO papers_fulltext (metadata_id, full_text) VALUES (?,?)""",
                (meta_id, full_text))
    conn.commit()

    out_file = os.path.join(TEXT_OUT_DIR, f"arxiv_{arxiv_id}.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    print("[arXiv] Saved:", out_file)

# ==============================
# MAIN EXECUTION
# ==============================
def main():
    print("🔍 PubMed & arXiv extraction starting…")
    # PubMed query
    query_pubmed = f"({SEARCH_KEYWORDS}) AND (pubmed pmc open access[filter])"
    pmids = Entrez.read(Entrez.esearch(db="pubmed", term=query_pubmed, retmax=PUBMED_MAX))["IdList"]
    for pmid in pmids:
        fetch_pubmed_fulltext(pmid)

    # arXiv query
    query_arxiv = f"all:{SEARCH_KEYWORDS}"
    arxiv_results = arxiv.Search(query=query_arxiv, max_results=ARXIV_MAX).results()
    for r in arxiv_results:
        aid = r.entry_id.split("/")[-1]
        process_arxiv_paper(aid)

    conn.close()
    print("🔚 Extraction complete!")

if __name__ == "__main__":
    main()
