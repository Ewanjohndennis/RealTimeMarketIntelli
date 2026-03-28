import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm
from tools.rag_tools import search_company_knowledge

SYSTEM = """
You are the Chief Intelligence Officer.

Merge analyst reports into an executive brief.

EXECUTIVE BRIEF:

Provide EXACTLY 5 bullet points.

Each bullet must:
- Be ONE complete sentence
- Be 100-120 words
- Contain specific insight (not generic labels)

Cover:
1. Market position (with reason)
2. Key strength (with explanation)
3. Key weakness (with implication)
4. Growth opportunity (with impact)
5. Risk (with consequence)

Avoid:
- single words
- vague terms like "leader", "strong", "good"
- repeating section names

Be sharp, specific, and analytical.
"""
def run(company, combined, knowledge=None):
    knowledge_text = knowledge or search_company_knowledge(
        company, "company strategy market positioning long term strategy"
    )
    return ask_llm(
        SYSTEM,
        f"""
Company: {company}

Background knowledge:
{knowledge_text}

News analysis:
{combined}
"""
    )