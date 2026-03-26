import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp.server.fastmcp import FastMCP
import yfinance as yf
import requests
from tools.rag_tools import search_company_knowledge
from tools.rag_tools import build_vector_store

build_vector_store()

mcp = FastMCP("market_tools")

@mcp.tool()
def get_stock_price(ticker: str):
    df = yf.download(ticker, period="1y", progress=False)
    df = df["Close"].tail(30)
    return df.to_dict()

@mcp.tool()
def company_knowledge(company: str, query: str):
    """
    Retrieve background knowledge about a company
    from the internal vector database.
    """
    return search_company_knowledge(company, query)

@mcp.tool()
def get_financials(ticker: str):
    t = yf.Ticker(ticker)
    info = t.fast_info
    return dict(info)

@mcp.tool()
def get_news(company: str):
    url = f"https://newsapi.org/v2/everything?q={company}"
    r = requests.get(url)
    return r.json()

if __name__ == "__main__":
    mcp.run()