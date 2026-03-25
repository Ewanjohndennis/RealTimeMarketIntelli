import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm

SYSTEM = """
You are a Competitor Analyst.
Compare the company against competitors using trends and news.
"""

def run(company, competitors, trends):

    return ask_llm(
        SYSTEM,
        f"""
Company: {company}
Competitors: {competitors}

Trends:
{trends}
"""
    )