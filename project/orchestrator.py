import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.news_agent import run as news_agent
from agents.competitor_agent import run as competitor_agent
from agents.financial_agent import run as financial_agent
from agents.chief_agent import run as chief_agent


def run_pipeline(context):

    company = context["company"]
    competitors = context["competitors"]
    news = context["news"]
    trends = context["trends"]
    financials = context["financials"]

    news_out = news_agent(company, news)

    comp_out = competitor_agent(
        company,
        competitors,
        trends
    )

    fin_out = financial_agent(
        company,
        financials
    )

    brief = chief_agent(
        company,
        news_out,
        comp_out,
        fin_out
    )

    return {
        "news": news_out,
        "competitor": comp_out,
        "financial": fin_out,
        "brief": brief
    }