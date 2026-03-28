import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm
from tools.rag_tools import search_company_knowledge

SYSTEM = """
You are a Competitor Analyst.
Compare the company against competitors using trends and news.
"""
def detect_competitors(company: str):
    prompt = f"""
List the top 3 direct competitors of {company}.
Return ONLY a comma-separated list.
"""
    response = ask_llm(prompt)
    import re
    competitors = re.split(r",|\n", response)
    return [c.strip() for c in competitors if c.strip()]

def run(company, competitors, trends, knowledge=None):
    knowledge_text = knowledge or search_company_knowledge(
        company, "products strategy market positioning competitors"
    )
    return ask_llm(
        SYSTEM,
        f"""
Company: {company}
Competitors: {competitors}

Background knowledge:
{knowledge_text}

Trends:
{trends}
"""
    )