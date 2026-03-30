from project.llm import ask_llm

def run(company, combined):

    SYSTEM = """
You are a strategy consultant.

Generate business recommendations based on company insights.
"""

    USER = f"""
Company: {company}

Insights:
{combined}

---

WHAT TO IMPROVE:

Provide EXACTLY 5 strategic recommendations.

Each must:
- Be exactly 60-80 words
- Include action + impact
- Be specific and practical

Format:
- [Action] → [Impact]
"""

    return ask_llm(SYSTEM, USER)