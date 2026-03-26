import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm
from agents.message import AgentMessage
from tools.rag_tools import search_company_knowledge
SYSTEM = """
You are a News Analyst.
Summarize opportunities and risks from news headlines.
"""

def run(company, news):

    knowledge = search_company_knowledge(company, "company strategy")

    headlines = "\n".join([
    f"{a['title']} — {a['snippet']}"
    for a in news
])

    result = ask_llm(
        SYSTEM,
        f"""
Company: {company}

Background Knowledge:
{knowledge}

News:
{headlines}
"""
    )

    return result