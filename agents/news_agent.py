import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm
from agents.message import AgentMessage
from tools.rag_tools import search_company_knowledge
SYSTEM = """
You are a News Analyst.

Analyze recent news and extract strategic implications for the company.

Do NOT summarize headlines. Instead, identify what the news means for the business.

OUTPUT FORMAT:

OPPORTUNITIES:
- ...
- ...
- ...
- ...

RISKS:
- ...
- ...
- ...
- ...

MARKET SIGNALS:
- ...
- ...
- ...
- ...

Rules:
- Exactly 4 bullets per section
- Each bullet ≤ 35 words
- Focus on impact (growth, competition, regulation, demand, sentiment)
- Avoid repeating the headline
- No generic statements
- No extra text outside sections
"""

def run(company, news, knowledge=None):
    knowledge_text = knowledge or search_company_knowledge(company, "company strategy")
    headlines = "\n".join([
        f"{a['title']} — {a['snippet']}"
        for a in news
    ])
    result = ask_llm(
        SYSTEM,
        f"""
Company: {company}

Background Knowledge:
{knowledge_text}

News:
{headlines}
"""
    )
    return result