import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ✅ Use fastmcp (not mcp)
from fastmcp import FastMCP

mcp = FastMCP("market_tools")


# 🔹 STOCK TOOL
@mcp.tool()
def get_stock_price(ticker: str):
    import yfinance as yf 

    df = yf.download(ticker, period="1y", progress=False)
    return df["Close"].tail(30).tolist()

@mcp.tool()
def company_knowledge(company: str, query: str):
    """
    Retrieve background knowledge about a company
    from the internal vector database.
    """
    from tools import rag_tools  # ✅ lazy import

    # Build only if needed
    rag_tools.build_vector_store()
    return rag_tools.search_company_knowledge(company, query)

@mcp.tool()
def get_financials(ticker: str):
    import yfinance as yf  # ✅ lazy import

    t = yf.Ticker(ticker)
    info = t.fast_info

    return dict(info)

@mcp.tool()
def get_news(company: str):
    import feedparser  # lazy import

    query = company.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}"

    feed = feedparser.parse(url)

    articles = []

    for entry in feed.entries[:5]:
        articles.append({
            "title": entry.title,
            "source": entry.source.get("title", "Unknown"),
            "link": entry.link
        })

    return articles

# 🔹 ENTRY POINT
if __name__ == "__main__":
    try:
        print("🚀 FastMCP server running...", flush=True)
        mcp.run()
    except Exception as e:
        print("❌ MCP SERVER CRASH:", str(e), flush=True)
        import traceback
        traceback.print_exc()