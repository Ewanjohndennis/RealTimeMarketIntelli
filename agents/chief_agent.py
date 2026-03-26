import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm
from tools.rag_tools import search_company_knowledge

SYSTEM = """
You are the Chief Intelligence Officer.

Merge analyst reports into an executive brief.

Sections:
1 Company Pulse
2 Competitive Position
3 Financial Health
4 Key Risks
5 Strategic Recommendations
"""

def run(company, news, comp, fin):

    knowledge = search_company_knowledge(
        company,
        "company strategy market positioning long term strategy"
    )

    return ask_llm(
        SYSTEM,
        f"""
Company: {company}

Background knowledge:
{knowledge}

News analysis:
{news}

Competitor analysis:
{comp}

Financial analysis:
{fin}
"""
    )