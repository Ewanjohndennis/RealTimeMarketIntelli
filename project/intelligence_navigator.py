import streamlit as st
import re


def render_intelligence_navigator(
    company: str,
    brief: str,
    news_out: str,
    comp_out: str,
    fin_out: str,
    improve_out: str,
    financials: dict,
    ticker_map: dict,
    competitors: list,
):
    st.markdown("### 🧭 Intelligence Navigator")
    st.caption("Select a question to get an instant insight from the report.")
    st.divider()

    # ── Question bank — maps label to a resolver function ─────────────────
    questions = {
        "📋 Give me the executive summary":           lambda: _executive_summary(brief),
        "📈 How is the stock performing?":            lambda: _stock_performance(company, financials, ticker_map),
        "💰 What are the key financial signals?":     lambda: _financial_signals(fin_out),
        "⚠️  What are the biggest risks?":            lambda: _risks(fin_out, brief),
        "⚔️  How are we positioned vs competitors?":  lambda: _competitor_position(comp_out, competitors),
        "🎯 What should the company prioritize?":     lambda: _priorities(improve_out),
        "🔍 What's happening in the news?":           lambda: _news_summary(news_out),
        "📊 What do the financials look like?":       lambda: _financials_snapshot(company, financials, ticker_map),
    }

    # ── Button grid — 2 columns ────────────────────────────────────────────
    keys = list(questions.keys())
    col1, col2 = st.columns(2)

    for i, label in enumerate(keys):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(label, use_container_width=True, key=f"nav_{i}"):
                st.session_state["nav_answer"] = questions[label]()
                st.session_state["nav_question"] = label

    # ── Answer panel ───────────────────────────────────────────────────────
    if st.session_state.get("nav_answer"):
        st.divider()
        st.markdown(f"**{st.session_state['nav_question']}**")
        st.info(st.session_state["nav_answer"])


# ── Resolvers ──────────────────────────────────────────────────────────────────

def _executive_summary(brief: str) -> str:
    if not brief:
        return "Executive brief not available yet."
    return brief.strip()


def _stock_performance(company: str, financials: dict, ticker_map: dict) -> str:
    ticker = ticker_map.get(company)
    if not ticker:
        return "Stock data not available for this company."
    fin = financials.get(ticker, {})
    if not fin:
        return "Financial data could not be retrieved."

    price   = fin.get("current_price", 0)
    high    = fin.get("52w_high", 0)
    low     = fin.get("52w_low", 0)
    pe      = fin.get("pe_ratio", 0)
    mcap    = fin.get("market_cap", 0)

    pct_from_high = ((price - high) / high * 100) if high else 0

    return (
        f"**{company} ({ticker})** is currently trading at **${price:.2f}**. "
        f"Over the past 52 weeks it has ranged from **${low:.2f}** to **${high:.2f}**, "
        f"sitting **{pct_from_high:.1f}% below its yearly high**. "
        f"Market cap stands at **${mcap/1e9:.1f}B** with a P/E ratio of **{pe:.1f}x**."
    )


def _financial_signals(fin_out: str) -> str:
    if not fin_out:
        return "Financial analysis not available."
    # Extract just the GROWTH SIGNALS section
    if "GROWTH SIGNALS:" in fin_out:
        section = fin_out.split("GROWTH SIGNALS:")[1]
        section = section.split("RISKS:")[0].strip()
        return f"**Growth Signals:**\n{section}"
    return fin_out.strip()


def _risks(fin_out: str, brief: str) -> str:
    risks = []

    # Pull RISKS section from financial agent
    if fin_out and "RISKS:" in fin_out:
        section = fin_out.split("RISKS:")[1].strip()
        risks.append(f"**Financial Risks:**\n{section[:600]}")

    # Pull risk bullet from brief (last bullet is always risk)
    if brief:
        bullets = [b.strip() for b in brief.strip().split("\n") if b.strip().startswith("-")]
        if bullets:
            risks.append(f"**Strategic Risk:**\n{bullets[-1]}")

    return "\n\n".join(risks) if risks else "Risk data not available."


def _competitor_position(comp_out: str, competitors: list) -> str:
    if not comp_out:
        return "Competitor analysis not available."
    comp_str = ", ".join(competitors) if competitors else "N/A"
    return f"**Competing against:** {comp_str}\n\n{comp_out.strip()[:800]}"


def _priorities(improve_out: str) -> str:
    if not improve_out:
        return "Strategic recommendations not available."
    # Return first 2 recommendations as the top priorities
    bullets = [b.strip() for b in improve_out.strip().split("\n") if b.strip().startswith("-")]
    if bullets:
        top = "\n".join(bullets[:2])
        return f"**Top 2 Strategic Priorities:**\n{top}"
    return improve_out.strip()[:600]


def _news_summary(news_out: str) -> str:
    if not news_out:
        return "News analysis not available."
    return news_out.strip()[:800]


def _financials_snapshot(company: str, financials: dict, ticker_map: dict) -> str:
    ticker = ticker_map.get(company)
    if not ticker:
        return "Financial data not available."
    fin = financials.get(ticker, {})
    if not fin:
        return "Could not retrieve financial data."

    rev     = fin.get("revenue_ttm", 0)
    margin  = fin.get("gross_margin", 0)
    op_mar  = fin.get("operating_margin", 0)
    roe     = fin.get("return_on_equity", 0)
    eps     = fin.get("eps", 0)
    de      = fin.get("debt_to_equity", 0)
    div     = fin.get("dividend_yield", 0)

    return (
        f"**{company} Financial Snapshot:**\n\n"
        f"- TTM Revenue: **${rev/1e9:.1f}B**\n"
        f"- Gross Margin: **{margin*100:.1f}%**\n"
        f"- Operating Margin: **{op_mar*100:.1f}%**\n"
        f"- Return on Equity: **{roe*100:.1f}%**\n"
        f"- EPS: **${eps:.2f}**\n"
        f"- Debt/Equity: **{de:.2f}**\n"
        f"- Dividend Yield: **{div*100:.2f}%**" if div else
        f"- TTM Revenue: **${rev/1e9:.1f}B**\n"
        f"- Gross Margin: **{margin*100:.1f}%**\n"
        f"- Operating Margin: **{op_mar*100:.1f}%**\n"
        f"- Return on Equity: **{roe*100:.1f}%**\n"
        f"- EPS: **${eps:.2f}**\n"
        f"- Debt/Equity: **{de:.2f}**"
    )