import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project.llm import ask_llm

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

def run(news, comp, fin):

    return ask_llm(
        SYSTEM,
        f"""
News analysis:
{news}

Competitor analysis:
{comp}

Financial analysis:
{fin}
"""
    )