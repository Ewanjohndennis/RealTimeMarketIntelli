import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm
from tools.rag_tools import search_company_knowledge

SYSTEM = """
You are a Financial Analyst.
Evaluate growth signals and risks.
Return EXACTLY in this format:

GROWTH SIGNALS:
- ...
- ...
- ...
- ...
- ...

RISKS:
- ...
- ...
- ...
- ...
- ...

Rules:
- Exactly 5 bullets per section
- Each bullet ≤ 100 words
- No markdown code blocks
- No extra text

IMPORTANT:
- DO NOT return JSON
- DO NOT use {}
- DO NOT use "growth_signals"
- Only plain text bullets
"""

def run(company, financials, knowledge=None):
    knowledge_text = knowledge or search_company_knowledge(
        company, "financial performance strategy business model"
    )
    return ask_llm(
        SYSTEM,
        f"""
Company: {company}

Background knowledge:
{knowledge_text}

Financial summary:
{financials}
"""
    )