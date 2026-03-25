import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm

SYSTEM = """
You are a Financial Analyst.
Evaluate growth signals and risks.
"""

def run(company, financials):

    return ask_llm(
        SYSTEM,
        f"""
Company: {company}

Financial summary:
{financials}
"""
    )