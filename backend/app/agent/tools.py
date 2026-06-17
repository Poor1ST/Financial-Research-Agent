import json
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
def fetch_price_history(ticker: str, period: str = "6mo") -> str:
    """Fetch historical price data with technical indicators (RSI, SMA, MACD, Bollinger Bands) for charting. Returns a concise summary for the LLM plus a CHART_REQUEST marker for the frontend."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            return f"No data found for ticker '{ticker}'."

        close = hist["Close"]
        rsi = ta.rsi(close, length=14)
        sma20 = ta.sma(close, length=20)
        sma50 = ta.sma(close, length=50)
        macd = ta.macd(close)
        bb = ta.bbands(close, length=20, std=2)

        latest = hist.iloc[-1]
        price = latest["Close"]
        prev = hist.iloc[-2]["Close"]
        change = price - prev
        change_pct = (change / prev) * 100
        vol_avg = int(hist["Volume"].tail(30).mean())
        bb_width = bb.iloc[-1, 2] - bb.iloc[-1, 0] if bb is not None and len(bb) > 0 else None
        macd_val = macd.iloc[-1, 0] if macd is not None and len(macd) > 0 else None
        macd_sig = macd.iloc[-1, 1] if macd is not None and len(macd) > 0 else None

        info = stock.info
        name = info.get("longName", ticker)
        direction = "up" if change >= 0 else "down"

        summary = (
            f"{name} ({ticker}) \u2014 {period} chart\n"
            f"Latest: ${price:.2f} ({change:+.2f}, {change_pct:+.2f}%), RSI(14): {rsi.iloc[-1]:.1f}\n"
            f"SMA(20): ${sma20.iloc[-1]:.2f}, SMA(50): ${sma50.iloc[-1]:.2f}\n"
        )
        if macd_val is not None:
            summary += f"MACD: {macd_val:+.2f}, Signal: {macd_sig:+.2f}\n"
        if bb_width is not None and pd.notna(bb_width):
            summary += f"Bollinger Band Width: ${bb_width:.2f}\n"
        summary += f"Volume (30d avg): {vol_avg:,}/day\n"
        summary += f"Trend: {direction.upper()} ({change_pct:+.2f}% over last session)"

        marker = json.dumps({"ticker": ticker, "period": period})
        summary += f"\n\n[CHART_REQUEST:{marker}]"
        return summary
    except Exception as e:
        return f"Error fetching chart data for {ticker}: {e}"


@tool
def generate_analysis_report(asset: str) -> str:
    """Generate a structured market analysis report for a given asset ticker."""
    return asset  # placeholder — agent will fill via structured output
