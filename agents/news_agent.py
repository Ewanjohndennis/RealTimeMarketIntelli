import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm
from agents.message import AgentMessage

SYSTEM = """
You are a News Analyst.
Summarize opportunities and risks from news headlines.
"""

def run(company, news):

    headlines = " | ".join([n["title"] for n in news])

    result = ask_llm(
        SYSTEM,
        f"Company: {company}\n\nNews:\n{headlines}"
    )

    return result