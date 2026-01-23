# this code works well for both the research paper

import os
import re
import sqlite3
import requests
from dotenv import load_dotenv
from Bio import Entrez
import arxiv
import pymupdf4llm
from pymupdf4llm import to_markdown

# =========================
# Load Email & API
# =========================
load_dotenv()
Entrez.email = os.getenv("NCBI_EMAIL", "")
API_KEY = os.getenv("NCBI_API_KEY", "")

if not Entrez.email:
    raise RuntimeError("NCBI_EMAIL must be set in .env")

# =========================
# Hard-coded config
# =========================
KEYWORDS = ["skin", "derma", "dermatology", "eczema"]
PUBMED_MAX = 30
ARXIV_MAX = 30

DB_PATH = "data_ar_pb/research.db"
TEXT_OUT = "data_ar_pb/fulltexts"
ARXIV_SRC = "data_ar_pb/arxiv_src"

if not KEYWORDS:
    raise RuntimeError("KEYWORDS must contain terms")

PUBMED_QUERY = "(" + " OR ".join(KEYWORDS) + ")"
ARXIV_QUERY = " OR ".join(KEYWORDS)

os.makedirs(TEXT_OUT, exist_ok=True)
os.makedirs(ARXIV_SRC, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS papers_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    paper_id TEXT UNIQUE,
    pmcid TEXT,
    doi TEXT,
    title TEXT,
    authors TEXT,
    journal TEXT,
    pub_date TEXT,
    url TEXT,
    file_path TEXT,
    abstract TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS papers_fulltext (
    metadata_id INTEGER,
    full_text TEXT,
    FOREIGN KEY(metadata_id) REFERENCES papers_metadata(id)
)
""")
conn.commit()

def sanitize(txt: str) -> str:
    return re.sub(r"\s+", " ", txt).strip()

def search_pubmed_oa(query: str, max_results: int):
    """
    Search PubMed with free full text and PMC OA subset filters.
    """
    # Use both free full text and PMC OA filters
    combined = f"{query} AND (pmc open access[sb] OR free full text[sb])"
    handle = Entrez.esearch(
        db="pubmed", term=combined, retmax=max_results, api_key=API_KEY
    )
    records = Entrez.read(handle)
    return records.get("IdList", [])

def fetch_pmc_fulltext_by_pmcid(pmcid: str):
    """
    Fetch full text from PMC using BioC XML.
    """
    xml_url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmcid}/unicode"
    r = requests.get(xml_url, timeout=30)
    if r.status_code == 200 and "<document>" in r.text:
        txt = r.text
        # remove tag noise
        txt = re.sub(r"<fig.*?</fig>", " ", txt, flags=re.DOTALL)
        txt = re.sub(r"<ref.*?</ref>", " ", txt, flags=re.DOTALL)
        txt = re.sub(r"<.*?>", " ", txt)
        return sanitize(txt)
    return ""

def store_pubmed(pmid: str):
    """
    For a PMID, attempt to get the corresponding PMCID (if any) and full text.
    """
    # Try converting to PMCID
    converter_url = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
    r = requests.get(converter_url, params={"ids": pmid, "format": "json"}, timeout=10)
    pmcid = ""
    if r.status_code == 200:
        recs = r.json().get("records", [])
        if recs:
            pmcid = recs[0].get("pmcid", "")

    if not pmcid:
        return  # skip if no full text resource

    full_text = fetch_pmc_fulltext_by_pmcid(pmcid)
    if not full_text:
        return

    # Now fetch metadata from PubMed
    try:
        handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml", api_key=API_KEY)
        rec = Entrez.read(handle)["PubmedArticle"][0]
    except Exception:
        return

    art = rec["MedlineCitation"]["Article"]
    title = sanitize(art.get("ArticleTitle", ""))
    authors = ", ".join(
        f'{a.get("LastName","")} {a.get("Initials","")}' for a in art.get("AuthorList", [])
        if a.get("LastName")
    )
    journal = art["Journal"]["Title"]
    abstract = sanitize(" ".join(art.get("Abstract", {}).get("AbstractText", [])))
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    year = art.get("ArticleDate", [{}])[0].get("Year", "")
    month = art.get("ArticleDate", [{}])[0].get("Month", "")
    day = art.get("ArticleDate", [{}])[0].get("Day", "")
    pub_date = f"{year}-{month}-{day}"

    file_path = os.path.join(TEXT_OUT, f"pubmed_{pmid}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    cur.execute("""
    INSERT OR IGNORE INTO papers_metadata
    (source,paper_id,pmcid,doi,title,authors,journal,pub_date,url,file_path,abstract)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, ("pubmed", pmid, pmcid, "", title, authors, journal, pub_date, url, file_path, abstract))
    conn.commit()

    cur.execute("SELECT id FROM papers_metadata WHERE paper_id=?", (pmid,))
    mid = cur.fetchone()[0]
    cur.execute("INSERT INTO papers_fulltext(metadata_id,full_text) VALUES (?,?)", (mid, full_text))
    conn.commit()

    print(f"[PubMed] {pmid} stored")

def fetch_arxiv_pdf(aid: str):
    """
    Download arXiv PDF and convert to markdown.
    """
    pdf_path = os.path.join(ARXIV_SRC, f"{aid}.pdf")
    r = requests.get(f"https://arxiv.org/pdf/{aid}.pdf", timeout=30)
    if r.status_code == 200:
        with open(pdf_path, "wb") as f:
            f.write(r.content)
        md = to_markdown(pdf_path)
        return sanitize(md)
    return ""

def store_arxiv(res):
    """
    Store arXiv metadata + full text.
    """
    aid = res.entry_id.split("/")[-1]
    full_text = fetch_arxiv_pdf(aid)
    if not full_text:
        return

    title = sanitize(res.title or "")
    authors = ", ".join(str(a) for a in res.authors)
    journal = res.journal_ref or ""
    pub_date = res.published.date().isoformat() if res.published else ""
    url = f"https://arxiv.org/abs/{aid}"
    abstract = sanitize(res.summary or "")

    file_path = os.path.join(TEXT_OUT, f"arxiv_{aid}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    cur.execute("""
    INSERT OR IGNORE INTO papers_metadata
    (source,paper_id,pmcid,doi,title,authors,journal,pub_date,url,file_path,abstract)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, ("arxiv", aid, "", res.doi or "", title, authors, journal, pub_date, url, file_path, abstract))
    conn.commit()

    cur.execute("SELECT id FROM papers_metadata WHERE paper_id=?", (aid,))
    mid = cur.fetchone()[0]
    cur.execute("INSERT INTO papers_fulltext(metadata_id,full_text) VALUES (?,?)", (mid, full_text))
    conn.commit()

    print(f"[arXiv] {aid} stored")

def main():
    print("Searching PubMed full text...")
    pmids = search_pubmed_oa(PUBMED_QUERY, PUBMED_MAX)
    for pmid in pmids:
        store_pubmed(pmid)

    print("Searching arXiv...")
    client = arxiv.Client()
    for res in client.results(arxiv.Search(query=ARXIV_QUERY, max_results=ARXIV_MAX)):
        store_arxiv(res)

    conn.close()
    print("Extraction completed")

if __name__ == "__main__":
    main()
