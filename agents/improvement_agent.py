from project.llm import ask_llm
def run(company, news_out, comp_out, fin_out):
    
    SYSTEM = """
You are a strategy consultant.

Generate business recommendations based on company insights.
"""

    USER = f"""
Company: {company}

News Insights:
{news_out}

Competitive Analysis:
{comp_out}

Financial Insights:
{fin_out}

---

WHAT TO IMPROVE:

Provide EXACTLY 5 strategic recommendations.

Each must:
- Be 100-120 words
- Include action + impact
- Be specific and practical

Format:
- [Action] → [Impact]
"""

    return ask_llm(SYSTEM, USER)