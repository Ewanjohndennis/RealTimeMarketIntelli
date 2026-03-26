import os
import requests
from bs4 import BeautifulSoup
import wikipedia

DATA_DIR = "data/knowledge"

SPECIAL_PAGES = {
    "Apple": "Apple Inc.",
    "Samsung": "Samsung",
    "Nike": "Nike, Inc.",
    "Tesla": "Tesla, Inc.",
}
def save_doc(name, company, text):

    path = os.path.join(DATA_DIR, f"{name}.txt")

    text = f"""
Company: {company}

{text}
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def ingest_wikipedia(company):

    try:
        page_title = SPECIAL_PAGES.get(company, company + " (company)")
        page = wikipedia.page(page_title, auto_suggest=False)

        text = page.content

        save_doc(company + "_wiki", company, text)

    except Exception:
        print("Wikipedia ingestion failed")

def ingest_company_site(url, name):

    try:
        r = requests.get(url, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(separator="\n")

        save_doc(name + "_site", text)

    except Exception:
        pass


def ingest_company(company):

    ingest_wikipedia(company)