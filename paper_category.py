#this file is fetching all the categories and sub categories of arxiv website
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import uvicorn
import requests
from bs4 import BeautifulSoup
import arxiv

URL = "https://arxiv.org/category_taxonomy"
HEADERS = {"User-Agent": "Mozilla/5.0"}

app = FastAPI()

def fetch_arxiv_categories():
    resp = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")

    categories = {}

    for h2 in soup.find_all("h2", class_="accordion-head"):
        main_cat = h2.get_text(strip=True)
        categories[main_cat] = {"display_name": main_cat, "sub": {}}

        body = h2.find_next("div", class_="accordion-body")
        if not body:
            continue

        for h4 in body.find_all("h4"):
            full_text = h4.get_text(" ", strip=True)
            cat_id = full_text.split(" ")[0]

            span = h4.find("span")
            if span:
                cat_name = span.get_text(strip=True).replace("(", "").replace(")", "")
            else:
                cat_name = full_text[len(cat_id):].strip()

            categories[main_cat]["sub"][cat_id] = cat_name

    return categories


# Load categories at startup
CATEGORIES = fetch_arxiv_categories()


def fetch_papers(category_id):
    search = arxiv.Search(
        query=f"cat:{category_id}",
        max_results=10,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    papers = []
    for r in search.results():
        papers.append({
            "title": r.title,
            "authors": ", ".join(a.name for a in r.authors),
            "id": r.get_short_id(),
            "url": r.entry_id
        })
    return papers


@app.get("/", response_class=HTMLResponse)
def home():
    html = """
    <html>
    <body>
    <h2>Select arXiv Category</h2>
    <form action="/search" method="post">
        <select name="category">
    """

    for main, data in CATEGORIES.items():
        html += f"<optgroup label='{main}'>"
        for sub_id, sub_name in data["sub"].items():
            html += f"<option value='{sub_id}'>{sub_id} — {sub_name}</option>"
        html += "</optgroup>"

    html += """
        </select><br><br>
        <button type="submit">Fetch Papers</button>
    </form>
    </body>
    </html>
    """
    return html


@app.post("/search", response_class=HTMLResponse)
def search(category: str = Form(...)):
    papers = fetch_papers(category)

    html = f"<html><body><h2> Papers for {category}</h2><ul>"

    for p in papers:
        html += f"""
        <li>
            <b>{p['title']}</b><br>
            Authors: {p['authors']}<br>
            ID: {p['id']}<br>
            <a href="{p['url']}" target="_blank">Open</a>
            <br><br>
        </li>
        """

    html += "</ul><a href='/'>Back</a></body></html>"
    return html


if __name__ == "__main__":
    uvicorn.run("paper_category:app", host="0.0.0.0", port=8000, reload=True)









# import requests
# from bs4 import BeautifulSoup
# import json

# URL = "https://arxiv.org/category_taxonomy"

# headers = {
#     "User-Agent": "Mozilla/5.0"
# }

# def fetch_arxiv_categories():
#     resp = requests.get(URL, headers=headers)
#     soup = BeautifulSoup(resp.text, "html.parser")

#     categories = {}

#     # 1) main category = <h2 class="accordion-head">
#     for h2 in soup.find_all("h2", class_="accordion-head"):
#         main_cat = h2.get_text(strip=True)
#         categories[main_cat] = {"display_name": main_cat, "sub": {}}

#         # 2) subcategories live inside the next <div class="accordion-body">
#         body = h2.find_next("div", class_="accordion-body")

#         if not body:
#             continue

#         # 3) each subcategory is <h4>cs.AI — <span>(Artificial Intelligence)</span></h4>
#         for h4 in body.find_all("h4"):
#             full_text = h4.get_text(" ", strip=True)

#             # Example: "cs.AI — (Artificial Intelligence)"
#             cat_id = full_text.split(" ")[0]

#             span = h4.find("span")
#             if span:
#                 cat_name = span.get_text(strip=True).strip("()")
#             else:
#                 cat_name = full_text[len(cat_id):].strip()

#             categories[main_cat]["sub"][cat_id] = cat_name

#     return categories


# if __name__ == "__main__":
#     result = fetch_arxiv_categories()
#     print(json.dumps(result, indent=2, ensure_ascii=False))

# URL = "https://arxiv.org/category_taxonomy"
# headers = {"User-Agent": "Mozilla/5.0"}

# def fetch_arxiv_categories():
#     resp = requests.get(URL, headers=headers)
#     soup = BeautifulSoup(resp.text, "html.parser")

#     categories = {}

#     for h2 in soup.find_all("h2", class_="accordion-head"):
#         main_cat = h2.get_text(strip=True)
#         categories[main_cat] = {"display_name": main_cat, "sub": {}}

#         body = h2.find_next("div", class_="accordion-body")
#         if not body:
#             continue

#         for h4 in body.find_all("h4"):
#             full_text = h4.get_text(" ", strip=True)

#             cat_id = full_text.split(" ")[0]

#             span = h4.find("span")
#             if span:
#                 cat_name = span.get_text(strip=True).strip("()")
#             else:
#                 cat_name = full_text[len(cat_id):].strip()

#             categories[main_cat]["sub"][cat_id] = cat_name

#     return categories


# def summarize(categories):
#     summary = {}
#     total_categories = len(categories)
#     total_subcategories = 0

#     for main, info in categories.items():
#         sub_count = len(info["sub"])
#         summary[main] = sub_count
#         total_subcategories += sub_count

#     return total_categories, total_subcategories, summary


# if __name__ == "__main__":
#     cats = fetch_arxiv_categories()

#     # Print full JSON (optional)
#     # print(json.dumps(cats, indent=2, ensure_ascii=False))

#     total_main, total_sub, stats = summarize(cats)

#     print("\n===== CATEGORY SUMMARY =====")
#     print(f"Total Main Categories: {total_main}")
#     print(f"Total Sub-Categories: {total_sub}\n")

#     print("Sub-category count for each main category:\n")
#     for main, count in stats.items():
#         print(f"{main}: {count}")
