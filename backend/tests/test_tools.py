import pytest
from app.agent.tools import (
    fetch_price_and_indicators,
    fetch_price_history,
    search_financial_news,
    query_documents,
    generate_analysis_report,
)


class TestFetchPriceAndIndicators:
    def test_valid_ticker_returns_formatted_data(self):
        result = fetch_price_and_indicators.invoke({"ticker": "AAPL"})
        assert "AAPL" in result.upper() or "Apple" in result
        assert "$" in result
        assert "RSI" in result
        assert "SMA" in result
        assert "Volume" in result

    def test_invalid_ticker_returns_error(self):
        result = fetch_price_and_indicators.invoke({"ticker": "ZZZZZZ"})
        assert "Error" in result or "No data" in result or "not found" in result.lower()


class TestSearchFinancialNews:
    def test_valid_query_returns_results(self):
        result = search_financial_news.invoke({"query": "Apple"})
        assert len(result) > 50


class TestQueryDocuments:
    def test_no_relevant_docs_when_db_empty(self, monkeypatch):
        import tempfile, shutil
        import app.rag.retriever

        tmpdir = tempfile.mkdtemp()
        try:
            monkeypatch.setattr(app.rag.retriever, "CHROMA_DIR", tmpdir)
            result = query_documents.invoke({"query": "nonexistent"})
            assert result == "No relevant documents found."
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestFetchPriceHistory:
    def test_valid_ticker_returns_chart_request_marker(self):
        result = fetch_price_history.invoke({"ticker": "AAPL"})
        assert "Apple Inc." in result or "AAPL" in result
        assert "Latest:" in result
        assert "RSI" in result
        assert "SMA" in result
        assert "[CHART_REQUEST:" in result
        assert '"ticker": "AAPL"' in result or '"ticker":"AAPL"' in result
        assert '"period": "6mo"' in result or '"period":"6mo"' in result

    def test_invalid_ticker_returns_error(self):
        result = fetch_price_history.invoke({"ticker": "ZZZZZZ"})
        assert "Error" in result or "No data" in result


class TestGenerateAnalysisReport:
    def test_returns_asset_string(self):
        result = generate_analysis_report.invoke({"asset": "AAPL"})
        assert result == "AAPL"

    def test_returns_any_ticker_unchanged(self):
        result = generate_analysis_report.invoke({"asset": "MSFT"})
        assert result == "MSFT"
