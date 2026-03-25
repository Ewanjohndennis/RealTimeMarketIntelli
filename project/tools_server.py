from mcp.server.fastmcp import FastMCP
import yfinance as yf
import requests

mcp = FastMCP("market_tools")

@mcp.tool()
def get_stock_price(ticker: str):
    df = yf.download(ticker, period="1y", progress=False)
    df = df["Close"].tail(30)
    return df.to_dict()

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


def start_mcp_server():
    mcp.run()


if __name__ == "__main__":
    start_mcp_server()