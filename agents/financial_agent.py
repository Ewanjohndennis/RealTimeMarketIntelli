import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm
from tools.rag_tools import search_company_knowledge

SYSTEM = """
You are a Financial Analyst.
Evaluate growth signals and risks.

"""

def run(company, financials):

    knowledge = search_company_knowledge(
        company,
        "financial performance strategy business model"
    )

    return ask_llm(
        SYSTEM,
        f"""
Company: {company}

Background knowledge:
{knowledge}

Financial summary:
{financials}
"""
    )