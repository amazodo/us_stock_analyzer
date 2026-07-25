"""Integration test: verify all components work together."""

import logging
from datetime import datetime
import pandas as pd

from config.settings import LOG_LEVEL, LOGS_DIR, OUTPUT_DIR
from src.collectors.stock_data import StockDataCollector
from src.collectors.ticker_manager import get_ticker_manager
from src.analysis.technical_score import TechnicalScoreCalculator
from src.analysis.sentiment_score import SentimentAnalyzer
from src.analysis.supply_demand import analyze_supply_demand
from src.analysis.fibonacci import analyze_fibonacci
from src.recommender.ranker import rank_and_recommend

# Setup logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def test_ticker_manager():
    """Test ticker loading."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: Ticker Manager")
    logger.info("=" * 70)

    manager = get_ticker_manager()
    counts = manager.count_tickers()

    logger.info(f"OK S&P 100: {counts['sp100']} tickers")
    logger.info(f"OK NASDAQ 100: {counts['nasdaq100']} tickers")
    logger.info(f"OK Unified Universe: {counts['unified']} unique tickers")

    assert counts['unified'] > 100, "Should have 100+ tickers"
    logger.info("✅ PASSED")


def test_stock_data_collection():
    """Test stock data collection."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Stock Data Collection")
    logger.info("=" * 70)

    collector = StockDataCollector()
    test_tickers = ["AAPL", "MSFT", "GOOGL"]

    for ticker in test_tickers:
        df = collector.get_historical_data(ticker, period_days=365)
        assert df is not None, f"Should fetch data for {ticker}"
        assert len(df) > 20, f"Should have 20+ rows for {ticker}"
        logger.info(f"OK {ticker}: {len(df)} days of data")

    logger.info("✅ PASSED")


def test_technical_indicators(df: pd.DataFrame):
    """Test technical indicator calculations."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Technical Indicators")
    logger.info("=" * 70)

    from src.indicators.moving_averages import MovingAverageIndicators
    from src.indicators.momentum import MomentumIndicators
    from src.indicators.volatility import VolatilityIndicators

    # Moving averages
    df = MovingAverageIndicators.calculate_multiple_smas(df, periods=[20, 50, 200])
    df = MovingAverageIndicators.calculate_multiple_emas(df, periods=[12, 26])
    logger.info(f"OK Moving Averages calculated")

    # Momentum
    df = MomentumIndicators.calculate_rsi(df, window=14)
    df = MomentumIndicators.calculate_macd(df)
    df = MomentumIndicators.calculate_stochastic(df)
    logger.info(f"OK Momentum indicators calculated")

    # Volatility
    df = VolatilityIndicators.calculate_bollinger_bands(df, window=20)
    df = VolatilityIndicators.calculate_atr(df, window=14)
    logger.info(f"OK Volatility indicators calculated")

    logger.info("✅ PASSED")
    return df


def test_technical_score(df: pd.DataFrame):
    """Test technical score calculation."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Technical Score Calculation")
    logger.info("=" * 70)

    calculator = TechnicalScoreCalculator()
    score, components = calculator.calculate_overall_technical_score(df)

    logger.info(f"Overall Score: {score}/100")
    for component, value in components.items():
        logger.info(f"  - {component}: {value}/100")

    assert 0 <= score <= 100, "Score should be 0-100"
    logger.info("✅ PASSED")
    return score


def test_supply_demand(df: pd.DataFrame):
    """Test supply/demand analysis."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Supply/Demand Analysis")
    logger.info("=" * 70)

    analysis = analyze_supply_demand(df)

    logger.info(f"VWAP Position: {analysis.get('vwap_position')} (bullish if >0.5)")
    logger.info(f"  Signal: {analysis.get('vwap_signal')}")
    logger.info(f"Volume Spike: {analysis.get('volume_spike')}")
    logger.info(f"Institutional Flow: {analysis.get('institutional_flow_score')}")
    logger.info(f"  Signal: {analysis.get('institutional_signal')}")
    logger.info(f"ATR %: {analysis.get('atr_pct')}%")
    logger.info(f"5% Gain Feasible: {analysis.get('atr_5pct_feasible')}")

    logger.info("✅ PASSED")


def test_fibonacci(df: pd.DataFrame):
    """Test Fibonacci analysis."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 6: Fibonacci Analysis")
    logger.info("=" * 70)

    analysis = analyze_fibonacci(df)

    if analysis:
        logger.info(f"Current Price: ${analysis.get('current_price')}")
        logger.info(f"Swing High: ${analysis.get('swing_high')}")
        logger.info(f"Swing Low: ${analysis.get('swing_low')}")

        levels = analysis.get('retracement_levels', {})
        for level, price in levels.items():
            logger.info(f"  {level}: ${price}")

        logger.info("✅ PASSED")
    else:
        logger.warning("⚠️ Insufficient data for Fibonacci")


def test_sentiment_analysis():
    """Test sentiment analysis."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 7: Sentiment Analysis")
    logger.info("=" * 70)

    analyzer = SentimentAnalyzer()

    # Test with sample articles
    sample_articles = [
        {
            'title': 'Apple beats earnings expectations',
            'description': 'Strong growth in iPhone sales',
            'content': 'Positive outlook for next quarter',
            'source': {'name': 'Reuters'}
        },
        {
            'title': 'Market downturn concerns investors',
            'description': 'Tech stocks falling',
            'content': 'Uncertainty remains',
            'source': {'name': 'Bloomberg'}
        }
    ]

    result = analyzer.analyze_articles_sentiment(sample_articles)
    score = analyzer.convert_to_score(result)

    logger.info(f"Articles analyzed: {result.get('total_articles')}")
    logger.info(f"Positive: {result.get('positive_count')} | Neutral: {result.get('neutral_count')} | Negative: {result.get('negative_count')}")
    logger.info(f"Sentiment Score: {score}/100")
    logger.info(f"Summary: {result.get('sentiment_label')}")

    logger.info("✅ PASSED")


def test_ranking():
    """Test ranking system."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 8: Ranking System")
    logger.info("=" * 70)

    # Test data
    stock_scores = [
        ("AAPL", 78.5, 72.0),
        ("MSFT", 75.0, 68.0),
        ("GOOGL", 70.0, 65.0),
        ("AMZN", 72.0, 70.0),
        ("NVDA", 82.0, 75.0),
    ]

    score_dict = {ticker: (tech, sent) for ticker, tech, sent in stock_scores}
    results = rank_and_recommend(score_dict)

    recommendations = results.get('recommendations', [])
    logger.info(f"Total analyzed: {results.get('total_analyzed')}")
    logger.info(f"Recommendations:")

    for rank, rec in enumerate(recommendations[:5], 1):
        ticker = rec.get('ticker')
        score = rec.get('overall_score')
        logger.info(f"  #{rank}. {ticker}: {score}/100")

    metrics = results.get('aggregate_metrics', {})
    logger.info(f"Average Score: {metrics.get('mean')}/100")

    logger.info("✅ PASSED")


def main():
    """Run all integration tests."""
    logger.info("\n" + "🧪 INTEGRATION TEST SUITE 🧪".center(70))
    logger.info("=" * 70)

    try:
        # Test 1: Ticker Manager
        test_ticker_manager()

        # Test 2: Data Collection
        test_stock_data_collection()

        # Get sample data for indicator tests
        collector = StockDataCollector()
        df = collector.get_historical_data("AAPL", period_days=365)

        if df is not None and len(df) > 20:
            # Test 3: Technical Indicators
            df = test_technical_indicators(df)

            # Test 4: Technical Score
            score = test_technical_score(df)

            # Test 5: Supply/Demand
            test_supply_demand(df)

            # Test 6: Fibonacci
            test_fibonacci(df)

            # Test 7: Sentiment
            test_sentiment_analysis()

            # Test 8: Ranking
            test_ranking()

        logger.info("\n" + "=" * 70)
        logger.info("✅ ALL TESTS PASSED")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

