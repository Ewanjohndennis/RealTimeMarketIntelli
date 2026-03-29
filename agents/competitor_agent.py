import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import re
from project.llm import ask_llm
from tools.rag_tools import search_company_knowledge

COMPETITOR_GROUPS = [
    ["Apple", "Samsung", "Google", "Xiaomi", "OnePlus"],
    ["Nike", "Adidas", "Puma", "New Balance", "Reebok"],
    ["Microsoft", "Google", "Apple", "Amazon", "Meta"],
    ["Tesla", "Rivian", "Ford", "GM", "BYD"],
    ["Netflix", "Disney", "Amazon", "HBO", "Apple"],
    ["Coca Cola", "Pepsi", "Red Bull", "Monster", "Sprite"],
    ["Intel", "AMD", "Nvidia", "Qualcomm", "Apple"],
    ["Infosys", "Wipro", "TCS", "HCL", "Accenture"],
]

def get_preset_competitors(company: str) -> list[str]:
    name = company.strip().lower()
    for group in COMPETITOR_GROUPS:
        group_lower = [c.lower() for c in group]
        if name in group_lower:
            idx = group_lower.index(name)
            return [c for c in group if c.lower() != name]
    return []  

SYSTEM = """
You are a Competitor Analyst.
Compare the company against competitors using trends and news.
"""
def detect_competitors(company: str):
    preset = get_preset_competitors(company)
    if preset:
        return preset
    prompt = f"""
List the top 3 direct competitors of {company}.
Return ONLY a comma-separated list.
"""
    response = ask_llm(prompt)

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