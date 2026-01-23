# this code is only for extracting text from pubmed for now (need to check)


import os
import re
import sqlite3
import requests
import tarfile
import tempfile
from Bio import Entrez
import arxiv
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Use pymupdf4llm for PDF -> text Markdown extraction
import pymupdf4llm
from pymupdf4llm import to_markdown

# ======================
# Load config
# ======================
load_dotenv()

Entrez.email = os.getenv("NCBI_EMAIL")
API_KEY = os.getenv("NCBI_API_KEY")
if not Entrez.email:
    raise ValueError("NCBI_EMAIL must be set in .env")

SEARCH_KEYWORDS = os.getenv(
    "SEARCH_KEYWORDS",
    "skin OR dermatology OR dermatitis OR eczema OR psoriasis OR melanoma"
)
PUBMED_MAX = int(os.getenv("PUBMED_MAX_RESULTS", "20"))
ARXIV_MAX = int(os.getenv("ARXIV_MAX_RESULTS", "20"))

DB_PATH = os.getenv("DATABASE_PATH", "data/research_both.db")
TEXT_OUT_DIR = os.getenv("TEXT_OUT_DIR", "data/fulltexts")
ARXIV_SRC_DIR = os.getenv("ARXIV_SRC_DIR", "data/arxiv_src")

os.makedirs(TEXT_OUT_DIR, exist_ok=True)
os.makedirs(ARXIV_SRC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ======================
# Setup SQLite
# ======================
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS papers_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    paper_id TEXT UNIQUE,
    pub_date TEXT,
    title TEXT,
    authors TEXT,
    journal TEXT,
    doi TEXT,
    url TEXT,
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

# ======================
# Utilities
# ======================
def sanitize_text(txt: str) -> str:
    return re.sub(r"\s+", " ", txt).strip()

# ======================
# PUBMED + PMC Full Text
# ======================
def convert_to_pmcid(pmid: str) -> str:
    # Use the PMC ID converter API to map PMIDs to PMCIDs
    url = f"https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?ids={pmid}&format=json"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        try:
            return r.json().get("records", [{}])[0].get("pmcid", "")
        except:
            pass
    return ""

def fetch_pmc_fulltext(pmcid: str) -> str:
    # Use PMC BioC full text API for open access articles
    # Note: BioC endpoint exists at:
    # https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/<PMCID>/unicode
    api_url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmcid}/unicode"
    try:
        r = requests.get(api_url, timeout=20)
        if r.status_code == 200:
            xml = r.text
            # strip tags, keep body
            xml = re.sub(r"<fig.*?</fig>", " ", xml, flags=re.DOTALL)
            xml = re.sub(r"<.*?>", " ", xml, flags=re.DOTALL)
            return sanitize_text(xml)
    except:
        pass
    return ""

def store_pubmed(pmid):
    try:
        handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml", api_key=API_KEY)
        rec = Entrez.read(handle)["PubmedArticle"][0]
    except:
        return

    art = rec["MedlineCitation"]["Article"]

    title = art.get("ArticleTitle", "")
    authors = []
    for a in art.get("AuthorList", []):
        if a.get("LastName"):
            authors.append(f"{a['LastName']} {a.get('Initials','')}")
    authors_str = ", ".join(authors)

    journal = art["Journal"]["Title"]

    pub_date = ""
    if "ArticleDate" in art and art["ArticleDate"]:
        d = art["ArticleDate"][0]
        pub_date = f"{d.get('Year','')}-{d.get('Month','')}-{d.get('Day','')}"
    elif art["Journal"]["JournalIssue"].get("PubDate"):
        pd = art["Journal"]["JournalIssue"]["PubDate"]
        pub_date = pd.get("Year", "")

    abstract = ""
    if "Abstract" in art:
        abstract = sanitize_text(" ".join(art["Abstract"]["AbstractText"]))

    doi = ""
    for aid in rec["PubmedData"]["ArticleIdList"]:
        if aid.attributes.get("IdType") == "doi":
            doi = str(aid)

    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    # Insert metadata
    cur.execute("""
    INSERT OR IGNORE INTO papers_metadata
    (source, paper_id, pub_date, title, authors, journal, doi, url, abstract)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    ("pubmed", pmid, pub_date, title, authors_str, journal, doi, url, abstract))
    conn.commit()

    cur.execute("SELECT id FROM papers_metadata WHERE paper_id=?", (pmid,))
    mid = cur.fetchone()[0]

    full_text = ""
    pmcid = convert_to_pmcid(pmid)
    if pmcid:
        full_text = fetch_pmc_fulltext(pmcid)
    if not full_text:
        full_text = abstract

    cur.execute("""
    INSERT INTO papers_fulltext (metadata_id, full_text) VALUES (?, ?)""",
    (mid, full_text))
    conn.commit()

    out_file = os.path.join(TEXT_OUT_DIR, f"pubmed_{pmid}.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"[PubMed] {pmid} extracted")

# ======================
# ARXIV Full Text Extraction
# ======================
def fetch_arxiv_html(arxiv_id):
    # Try multiple HTML sources (including ar5iv)
    urls = [
        f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}",
        f"https://ar5iv.org/html/{arxiv_id}",
        f"https://arxiv.org/html/{arxiv_id}"
    ]
    for u in urls:
        try:
            r = requests.get(u, timeout=20)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                return sanitize_text(soup.get_text(separator="\n"))
        except:
            pass
    return ""

def fetch_arxiv_latex(arxiv_id):
    path = os.path.join(ARXIV_SRC_DIR, f"{arxiv_id}.tar.gz")
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            tempdir = tempfile.mkdtemp(prefix=arxiv_id+"_src_")
            with tarfile.open(path, "r:gz") as tar:
                tar.extractall(path=tempdir)
            all_text = []
            for root, _, files in os.walk(tempdir):
                for nm in files:
                    if nm.endswith(".tex"):
                        with open(os.path.join(root, nm), "r", encoding="utf-8", errors="ignore") as te:
                            txt = te.read()
                            all_text.append(sanitize_text(re.sub(r"\\.*?{|}", " ", txt)))
            return " ".join(all_text)
    except:
        pass
    return ""

def fetch_arxiv_pdf(arxiv_id):
    temp_pdf = os.path.join(ARXIV_SRC_DIR, f"{arxiv_id}.pdf")
    try:
        r = requests.get(f"https://arxiv.org/pdf/{arxiv_id}.pdf", timeout=30)
        if r.status_code == 200:
            with open(temp_pdf, "wb") as f:
                f.write(r.content)
            md = to_markdown(temp_pdf)
            return sanitize_text(md)
    except:
        pass
    return ""

def store_arxiv(arxiv_id):
    client = arxiv.Client()
    result = next(client.results(arxiv.Search(query=f"id:{arxiv_id}", max_results=1)), None)
    if not result:
        return

    title = sanitize_text(result.title)
    authors = ", ".join(str(a) for a in result.authors)
    pub_date = result.published.date().isoformat() if result.published else ""
    journal = result.journal_ref or ""
    doi = result.doi or ""
    url = f"https://arxiv.org/abs/{arxiv_id}"

    cur.execute("""
    INSERT OR IGNORE INTO papers_metadata
    (source, paper_id, pub_date, title, authors, journal, doi, url, abstract)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    ("arxiv", arxiv_id, pub_date, title, authors, journal, doi, url, ""))

    conn.commit()
    cur.execute("SELECT id FROM papers_metadata WHERE paper_id=?", (arxiv_id,))
    mid = cur.fetchone()[0]

    full_text = fetch_arxiv_html(arxiv_id)
    if not full_text:
        full_text = fetch_arxiv_latex(arxiv_id)
    if not full_text:
        full_text = fetch_arxiv_pdf(arxiv_id)
    if not full_text:
        full_text = sanitize_text(result.summary or "")

    cur.execute("INSERT INTO papers_fulltext(metadata_id, full_text) VALUES (?, ?)", (mid, full_text))
    conn.commit()

    out_file = os.path.join(TEXT_OUT_DIR, f"arxiv_{arxiv_id}.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"[arXiv] {arxiv_id} extracted")

# ======================
# MAIN
# ======================
def main():
    print("Extracting PubMed…")
    h = Entrez.esearch(db="pubmed", term=f"({SEARCH_KEYWORDS}) AND free full text[sb]", retmax=PUBMED_MAX, api_key=API_KEY)
    pmids = Entrez.read(h).get("IdList", [])
    for pm in pmids:
        store_pubmed(pm)

    print("Extracting arXiv…")
    client = arxiv.Client()
    for item in client.results(arxiv.Search(query=f"all:{SEARCH_KEYWORDS}", max_results=ARXIV_MAX)):
        pid = item.entry_id.split("/")[-1]
        store_arxiv(pid)

    conn.close()
    print("✔ Extraction complete.")

if __name__ == "__main__":
    main()
