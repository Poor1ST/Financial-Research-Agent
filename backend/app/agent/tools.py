from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
import yfinance as yf
import pandas as pd
import pandas_ta as ta


@tool
def fetch_price_and_indicators(ticker: str) -> str:
    """Fetch live price, RSI, and SMA for a given stock ticker (e.g. AAPL, MSFT, TSLA)."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")

        if hist.empty:
            return f"No data found for ticker '{ticker}'."

        close = hist["Close"]
        rsi = ta.rsi(close, length=14)
        sma_20 = ta.sma(close, length=20)
        sma_50 = ta.sma(close, length=50)

        latest = hist.iloc[-1]
        price = latest["Close"]
        change = latest["Close"] - hist.iloc[-2]["Close"]
        change_pct = (change / hist.iloc[-2]["Close"]) * 100

        info = stock.info
        name = info.get("longName", ticker)

        return (
            f"{name} ({ticker})\n"
            f"Price: ${price:.2f} ({change:+.2f}, {change_pct:+.2f}%)\n"
            f"RSI(14): {rsi.iloc[-1]:.1f}\n"
            f"SMA(20): ${sma_20.iloc[-1]:.2f}\n"
            f"SMA(50): ${sma_50.iloc[-1]:.2f}\n"
            f"Volume: {int(latest['Volume']):,}"
        )
    except Exception as e:
        return f"Error fetching data for {ticker}: {e}"


@tool
def search_financial_news(query: str) -> str:
    """Search the web for latest financial news on a given topic or company."""
    search = DuckDuckGoSearchRun()
    return search.run(f"financial news {query}")


@tool
def query_documents(query: str) -> str:
    """Query user-uploaded financial documents (PDFs, reports, notes) using RAG."""
    from app.rag.retriever import get_retriever

    retriever = get_retriever()
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant documents found."
    return "\n\n".join(doc.page_content[:1000] for doc in docs[:3])


@tool
def generate_analysis_report(asset: str) -> str:
    """Generate a structured market analysis report for a given asset ticker."""
    return asset  # placeholder — agent will fill via structured output
