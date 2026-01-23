# Jan 16, 2026

# import os
# import re
# import sqlite3
# import requests
# import tarfile
# import tempfile
# from Bio import Entrez
# import arxiv
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv

# import pymupdf4llm
# from pymupdf4llm import to_markdown

# # Load environment
# load_dotenv()

# Entrez.email = os.getenv("NCBI_EMAIL")
# API_KEY = os.getenv("NCBI_API_KEY")
# if not Entrez.email:
#     raise ValueError("NCBI_EMAIL is required")

# SEARCH_KEYWORDS = os.getenv("SEARCH_KEYWORDS","")
# PUBMED_MAX=int(os.getenv("PUBMED_MAX_RESULTS","20"))
# ARXIV_MAX=int(os.getenv("ARXIV_MAX_RESULTS","20"))

# DB_PATH=os.getenv("DATABASE_PATH","data_/research_both.db")
# TEXT_OUT=os.getenv("TEXT_OUT_DIR","data_/fulltexts")
# SRC_DIR=os.getenv("ARXIV_SRC_DIR","data_/arxiv_src")

# os.makedirs(TEXT_OUT,exist_ok=True)
# os.makedirs(SRC_DIR,exist_ok=True)
# os.makedirs(os.path.dirname(DB_PATH),exist_ok=True)

# conn=sqlite3.connect(DB_PATH)
# cur=conn.cursor()

# # create tables
# cur.execute("""
# CREATE TABLE IF NOT EXISTS papers_metadata (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     source TEXT,
#     paper_id TEXT UNIQUE,
#     pmcid TEXT,
#     doi TEXT,
#     title TEXT,
#     authors TEXT,
#     journal TEXT,
#     pub_date TEXT,
#     url TEXT,
#     abstract TEXT
# );""")
# cur.execute("""
# CREATE TABLE IF NOT EXISTS papers_fulltext (
#     metadata_id INTEGER,
#     full_text TEXT,
#     FOREIGN KEY(metadata_id) REFERENCES papers_metadata(id)
# );""")
# conn.commit()

# def sanitize_text(txt):
#     return re.sub(r"\s+", " ", txt).strip()

# # PubMed article -> PMC Open Access fetch
# def convert_to_pmcid(pmid):
#     url=f"https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?ids={pmid}&format=json"
#     r=requests.get(url,timeout=10)
#     if r.status_code==200:
#         try:
#             return r.json().get("records",[{}])[0].get("pmcid","")
#         except:
#             pass
#     return ""

# def fetch_pmc_fulltext_bioc(pmid,pmcid):
#     xml_url=f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmcid}/unicode"
#     try:
#         r=requests.get(xml_url,timeout=20)
#         if r.status_code==200 and "<document>" in r.text:
#             txt=re.sub(r"<fig.*?</fig>"," ",r.text,flags=re.DOTALL)
#             txt=re.sub(r"<.*?>"," ",txt,flags=re.DOTALL)
#             return sanitize_text(txt)
#     except:
#         pass
#     return ""

# def store_pubmed(pmid):
#     # metadata via Entrez Efetch
#     try:
#         handle=Entrez.efetch(db="pubmed",id=pmid,retmode="xml",api_key=API_KEY)
#         rec=Entrez.read(handle)["PubmedArticle"][0]
#     except:
#         return

#     art=rec["MedlineCitation"]["Article"]
#     title=art.get("ArticleTitle","")
#     authors=", ".join([f'{a["LastName"]} {a.get("Initials","")}' for a in art.get("AuthorList",[]) if a.get("LastName")])
#     journal=art["Journal"]["Title"]
#     abstract=""
#     if "Abstract" in art:
#         abstract=sanitize_text(" ".join(art["Abstract"]["AbstractText"]))

#     pub_date=""
#     if "ArticleDate" in art and art["ArticleDate"]:
#         d=art["ArticleDate"][0]
#         # pub_date=f\"{d.get('Year','')}-{d.get('Month','')}-{d.get('Day','')}\"
#         pub_date = f"{d.get('Year','')}-{d.get('Month','')}-{d.get('Day','')}"

#     else:
#         try:
#             pd=art["Journal"]["JournalIssue"]["PubDate"]
#             pub_date=pd.get("Year","")
#         except:
#             pub_date=""
#     doi=""
#     for aid in rec["PubmedData"]["ArticleIdList"]:
#         if aid.attributes.get("IdType")=="doi":
#             doi=str(aid)

#     pmcid=convert_to_pmcid(pmid)
#     url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

#     cur.execute("""
#     INSERT OR IGNORE INTO papers_metadata
#     (source,paper_id,pmcid,doi,title,authors,journal,pub_date,url,abstract)
#     VALUES (?,?,?,?,?,?,?,?,?,?)""",
#     ("pubmed",pmid,pmcid,doi,title,authors,journal,pub_date,url,abstract))
#     conn.commit()
#     cur.execute("SELECT id FROM papers_metadata WHERE paper_id=?", (pmid,))
#     mid=cur.fetchone()[0]

#     full_text=""
#     if pmcid:
#         full_text=fetch_pmc_fulltext_bioc(pmid,pmcid)
#     if not full_text:
#         full_text=abstract

#     cur.execute("INSERT INTO papers_fulltext(metadata_id,full_text) VALUES (?,?)",(mid,full_text))
#     conn.commit()
#     out=os.path.join(TEXT_OUT,f"pubmed_{pmid}.txt")
#     with open(out,"w",encoding="utf-8") as f:
#         f.write(full_text)
#     print(f"[PubMed] {pmid} done")

# def fetch_arxiv_html(aid):
#     for u in [f"https://ar5iv.labs.arxiv.org/html/{aid}",f"https://ar5iv.org/html/{aid}",f"https://arxiv.org/html/{aid}"]:
#         try:
#             r=requests.get(u,timeout=15)
#             if r.status_code==200:
#                 return sanitize_text(BeautifulSoup(r.text,"html.parser").get_text("\n"))
#         except:
#             pass
#     return ""

# def fetch_arxiv_latex(aid):
#     path=os.path.join(SRC_DIR,f"{aid}.tar.gz")
#     r=requests.get(f"https://arxiv.org/e-print/{aid}",timeout=20)
#     if r.status_code==200:
#         with open(path,"wb") as f: f.write(r.content)
#         temp=tempfile.mkdtemp(prefix=aid+"_")
#         with tarfile.open(path,"r:gz") as tar: tar.extractall(temp)
#         alltxt=[]
#         for root,_,files in os.walk(temp):
#             for nm in files:
#                 if nm.endswith(".tex"):
#                     txt=open(os.path.join(root,nm),encoding="utf-8",errors="ignore").read()
#                     alltxt.append(sanitize_text(re.sub(r"\\.*?{|}"," ",txt)))
#         return " ".join(alltxt)
#     return ""

# def fetch_arxiv_pdf(aid):
#     outp=os.path.join(SRC_DIR,f"{aid}.pdf")
#     try:
#         r=requests.get(f"https://arxiv.org/pdf/{aid}.pdf",timeout=20)
#         if r.status_code==200:
#             with open(outp,"wb") as f: f.write(r.content)
#             md=to_markdown(outp)
#             return sanitize_text(md)
#     except:
#         pass
#     return ""

# def store_arxiv(aid):
#     client=arxiv.Client()
#     res=next(client.results(arxiv.Search(query=f"id:{aid}",max_results=1)),None)
#     if not res: return
#     title=sanitize_text(res.title)
#     authors=", ".join(str(a) for a in res.authors)
#     pub_date=res.published.date().isoformat() if res.published else ""
#     journal=res.journal_ref or ""
#     doi=res.doi or ""
#     url=f"https://arxiv.org/abs/{aid}"
#     abstract=sanitize_text(res.summary or "")

#     cur.execute("""
#     INSERT OR IGNORE INTO papers_metadata
#     (source,paper_id,pmcid,doi,title,authors,journal,pub_date,url,abstract)
#     VALUES (?,?,?,?,?,?,?,?,?,?)""",
#     ("arxiv",aid,"",doi,title,authors,journal,pub_date,url,abstract))
#     conn.commit()
#     cur.execute("SELECT id FROM papers_metadata WHERE paper_id=?", (aid,))
#     mid=cur.fetchone()[0]

#     text=fetch_arxiv_html(aid) or fetch_arxiv_latex(aid) or fetch_arxiv_pdf(aid) or abstract
#     cur.execute("INSERT INTO papers_fulltext(metadata_id,full_text) VALUES (?,?)",(mid,text))
#     conn.commit()
#     fout=os.path.join(TEXT_OUT,f"arxiv_{aid}.txt")
#     with open(fout,"w",encoding="utf-8") as f: f.write(text)
#     print(f"[arXiv] {aid} done")

# def main():
#     # PubMed OA subset
#     q=f"({SEARCH_KEYWORDS}) AND pubmed pmc open access[sb]"
#     h=Entrez.esearch(db="pubmed",term=q,retmax=PUBMED_MAX,api_key=API_KEY)
#     pmids=Entrez.read(h).get("IdList",[])
#     for pm in pmids: store_pubmed(pm)

#     # arXiv
#     aclient=arxiv.Client()
#     for itm in aclient.results(arxiv.Search(query=f"all:{SEARCH_KEYWORDS}",max_results=ARXIV_MAX)):
#         aid=itm.entry_id.split("/")[-1]
#         store_arxiv(aid)

#     conn.close()
#     print("Extraction completed")

# if __name__=="__main__":
#     main()



# Code 2
# in this code arxiv papers are fetched properly text is extracted well but the issue is in the pubmed as the text and papers are not stored.
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
# Load Email & API Key
# =========================
load_dotenv()

Entrez.email = os.getenv("NCBI_EMAIL", "")
API_KEY = os.getenv("NCBI_API_KEY", "")

if not Entrez.email:
    raise RuntimeError("NCBI_EMAIL must be set in the .env file")

# =========================
# Hard-coded Config
# =========================

# Keywords for search (list of terms)
KEYWORDS = ["skin", "derma", "dermatology", "eczema"]

# How many results to fetch
PUBMED_MAX = 30
ARXIV_MAX = 30

# Output locations (hard-coded)
DB_PATH = "data_/research.db"
TEXT_OUT = "data_/fulltexts"
ARXIV_SRC = "data_/arxiv_src"

# Build safe query strings
if not KEYWORDS:
    raise RuntimeError("KEYWORDS list must contain at least one keyword")

PUBMED_QUERY = "(" + " OR ".join(KEYWORDS) + ")"
ARXIV_QUERY = " OR ".join(KEYWORDS)

print("Running extraction with keywords:", KEYWORDS)

# =========================
# Prepare directories
# =========================
os.makedirs(TEXT_OUT, exist_ok=True)
os.makedirs(ARXIV_SRC, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# =========================
# Initialize SQLite
# =========================
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

# =========================
# Utility sanitizer
# =========================
def sanitize(txt: str) -> str:
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

# =========================
# PubMed / PMC functions
# =========================
def search_pubmed_oa(query: str, max_results: int):
    q = f"{query} AND pmc open access[sb]"
    handle = Entrez.esearch(db="pubmed", term=q, retmax=max_results, api_key=API_KEY)
    res = Entrez.read(handle)
    return res.get("IdList", [])

def pmid_to_pmcid(pmid: str):
    url = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
    r = requests.get(url, params={"ids": pmid, "format": "json"}, timeout=10)
    if r.status_code == 200:
        recs = r.json().get("records", [])
        if recs and recs[0].get("pmcid"):
            return recs[0]["pmcid"]
    return None

def fetch_pmc_fulltext(pmcid: str):
    xml_url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmcid}/unicode"
    r = requests.get(xml_url, timeout=20)
    if r.status_code != 200 or "<document>" not in r.text:
        return ""
    xml_text = r.text
    xml_text = re.sub(r"<fig.*?</fig>", " ", xml_text, flags=re.DOTALL)
    xml_text = re.sub(r"<ref.*?</ref>", " ", xml_text, flags=re.DOTALL)
    xml_text = re.sub(r"<.*?>", " ", xml_text)
    return sanitize(xml_text)

def store_pubmed(pmid: str):
    pmcid = pmid_to_pmcid(pmid)
    if not pmcid:
        return

    full_text = fetch_pmc_fulltext(pmcid)
    if not full_text:
        return

    handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml", api_key=API_KEY)
    rec = Entrez.read(handle)["PubmedArticle"][0]
    art = rec["MedlineCitation"]["Article"]

    title = sanitize(art.get("ArticleTitle", ""))
    authors = ", ".join(f'{a["LastName"]} {a.get("Initials","")}' for a in art.get("AuthorList", []) if a.get("LastName"))
    journal = art["Journal"]["Title"]
    abstract = sanitize(" ".join(art.get("Abstract", {}).get("AbstractText", [])))
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

    year, month, day = "", "", ""
    if art.get("ArticleDate"):
        d = art["ArticleDate"][0]
        year, month, day = d.get("Year",""), d.get("Month",""), d.get("Day","")

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
    cur.execute("INSERT INTO papers_fulltext(metadata_id, full_text) VALUES (?,?)", (mid, full_text))
    conn.commit()

    print(f"[PubMed] {pmid} stored")

# =========================
# arXiv functions
# =========================
def fetch_arxiv_pdf(aid: str):
    pdf_path = os.path.join(ARXIV_SRC, f"{aid}.pdf")
    r = requests.get(f"https://arxiv.org/pdf/{aid}.pdf", timeout=20)
    if r.status_code != 200:
        return ""
    with open(pdf_path, "wb") as f:
        f.write(r.content)
    md_text = to_markdown(pdf_path)
    return sanitize(md_text)

def store_arxiv(res):
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
    cur.execute("INSERT INTO papers_fulltext(metadata_id, full_text) VALUES (?,?)", (mid, full_text))
    conn.commit()

    print(f"[arXiv] {aid} stored")

# =========================
# Main execution
# =========================
def main():
    print(f"Searching PubMed: {PUBMED_QUERY}")
    pmids = search_pubmed_oa(PUBMED_QUERY, PUBMED_MAX)
    for pmid in pmids:
        store_pubmed(pmid)

    print(f"Searching arXiv: {ARXIV_QUERY}")
    client = arxiv.Client()
    search = arxiv.Search(query=ARXIV_QUERY, max_results=ARXIV_MAX)
    for res in client.results(search):
        store_arxiv(res)

    conn.close()
    print("Extraction completed")

if __name__ == "__main__":
    main()
