import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from concurrent.futures import ThreadPoolExecutor, as_completed
from agents.news_agent       import run as news_agent
from agents.competitor_agent import run as competitor_agent, detect_competitors
from agents.financial_agent  import run as financial_agent
from agents.chief_agent      import run as chief_agent
from agents.improvement_agent import run as improvement_agent
from tools.rag_tools import search_company_knowledge


def run_pipeline(context: dict) -> dict:
    company = context["company"]

    if context.get("task") == "detect_competitors":
        return {"competitors": detect_competitors(company)}

    competitors = context["competitors"]
    news        = context["news"]
    trends      = context["trends"]
    financials  = context["financials"]

    knowledge = search_company_knowledge(
        company,
        "strategy market positioning competitors financial performance"
    )

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_news = ex.submit(news_agent,       company, news,        knowledge)
        f_comp = ex.submit(competitor_agent, company, competitors, trends, knowledge)
        f_fin  = ex.submit(financial_agent,  company, financials,  knowledge)

    news_out = f_news.result()
    comp_out = f_comp.result()
    fin_out  = f_fin.result()

    def _trim(text: str, max_chars: int = 800) -> str:
        return text[:max_chars] + "…" if len(text) > max_chars else text

    combined = (
        f"NEWS:\n{_trim(news_out)}\n\n"
        f"COMPETITOR:\n{_trim(comp_out)}\n\n"
        f"FINANCIALS:\n{_trim(fin_out)}"
    )

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_brief   = ex.submit(chief_agent,       company, combined, knowledge)
        f_improve = ex.submit(improvement_agent, company, combined)

    return {
        "news":        news_out,
        "competitor":  comp_out,
        "financial":   fin_out,
        "brief":       f_brief.result(),
        "improvement": f_improve.result(),
    }