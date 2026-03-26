import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm
from tools.rag_tools import search_company_knowledge

SYSTEM = """
You are a Competitor Analyst.
Compare the company against competitors using trends and news.
"""

def run(company, competitors, trends):

    knowledge = search_company_knowledge(
        company,
        "products strategy market positioning competitors"
    )

    return ask_llm(
        SYSTEM,
        f"""
Company: {company}
Competitors: {competitors}

Background knowledge:
{knowledge}

Trends:
{trends}
"""
    )