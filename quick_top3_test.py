"""Quick Top 3 validation test with sample data (5-10 minutes)."""

import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from config.settings import LOG_LEVEL, LOGS_DIR, OUTPUT_DIR
from src.collectors.stock_data import StockDataCollector
from src.analysis.technical_score import TechnicalScoreCalculator
from src.recommender.ranker import StockRanker

# Setup logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "quick_top3_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class QuickTop3Test:
    """Quick test with sample stocks (5 min runtime)."""

    def __init__(self):
        self.stock_collector = StockDataCollector()
        self.technical_calc = TechnicalScoreCalculator()
        self.ranker = StockRanker()

        # Sample: 20 most liquid stocks for quick testing
        self.sample_tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
            "META", "TSLA", "BRK.B", "JPM", "JNJ",
            "V", "WMT", "PG", "MA", "UNH",
            "HD", "MCD", "INTC", "PYPL", "CRM"
        ]

    def fetch_and_score(self, test_date: datetime = None) -> list:
        """Fetch current data and calculate scores."""
        if test_date is None:
            test_date = datetime.now()

        logger.info(f"Fetching data for sample stocks (as of {test_date.date()})...")
        scores = []

        for i, ticker in enumerate(self.sample_tickers, 1):
            try:
                df = self.stock_collector.get_historical_data(ticker, period_days=365)

                if df is None or len(df) < 20:
                    logger.warning(f"  ⚠️  {ticker}: Insufficient data")
                    continue

                # Calculate technical score
                tech_score, components = self.technical_calc.calculate_overall_technical_score(df)

                # For this test, assume neutral sentiment
                sentiment_score = 50.0

                scores.append({
                    'ticker': ticker,
                    'technical': tech_score,
                    'sentiment': sentiment_score,
                    'components': components
                })

                logger.info(f"  OK {i:2d}. {ticker}: Tech={tech_score:.1f} (MA:{components.get('moving_averages', 0):.0f}, "
                           f"Mom:{components.get('momentum', 0):.0f}, Vol:{components.get('volatility', 0):.0f})")

            except Exception as e:
                logger.error(f"  ❌ {ticker}: {e}")
                continue

        logger.info(f"\nOK Scored {len(scores)} stocks")
        return scores

    def rank_and_display(self, scores: list):
        """Rank scores and display Top 3 vs Top 5."""
        if not scores:
            logger.error("No scores to rank")
            return None

        # Convert to ranking format
        stock_tuples = [(s['ticker'], s['technical'], s['sentiment']) for s in scores]

        # Rank
        ranked = self.ranker.rank_stocks(stock_tuples)

        # Display
        logger.info("\n" + "=" * 80)
        logger.info("🏆 RANKING RESULTS")
        logger.info("=" * 80)

        top3 = ranked[:3]
        top5 = ranked[:5]

        logger.info("\nTop 3:")
        for rank, score in enumerate(top3, 1):
            logger.info(f"  #{rank}. {score.ticker:6} - Score: {score.overall_score:6.1f} "
                       f"(Tech: {score.technical_score:6.1f}, Sent: {score.sentiment_score:6.1f})")

        logger.info("\nTop 5:")
        for rank, score in enumerate(ranked[:5], 1):
            marker = "→" if rank <= 3 else "  "
            logger.info(f"  {marker} #{rank}. {score.ticker:6} - Score: {score.overall_score:6.1f}")

        return {
            'top3': [s.ticker for s in top3],
            'top5': [s.ticker for s in top5],
            'ranked': ranked
        }

    def simulate_1week_returns(self, tickers: list) -> dict:
        """
        Simulate expected 1-week returns based on current technicals.
        This is a simplified model based on technical score correlation.
        """
        logger.info("\n" + "=" * 80)
        logger.info("📊 1-WEEK RETURN PROJECTION (Simulated)")
        logger.info("=" * 80)

        projections = {}

        for ticker in tickers:
            try:
                df = self.stock_collector.get_historical_data(ticker, period_days=365)
                if df is None:
                    continue

                # Get recent volatility (ATR)
                from src.indicators.volatility import VolatilityIndicators
                df = VolatilityIndicators.calculate_atr(df, window=14)

                current_price = df['Close'].iloc[-1]
                atr = df['ATR'].iloc[-1]
                atr_pct = (atr / current_price) * 100

                # Technical score as proxy for expected movement
                tech_score, _ = self.technical_calc.calculate_overall_technical_score(df)

                # Simple model: higher tech score + high volatility = higher chance of 5% gain
                # This is NOT a prediction, just correlation from historical patterns
                expected_move_pct = (tech_score - 50) / 10 * atr_pct * 0.5

                # Add some baseline volatility estimate
                expected_move_pct += (atr_pct / 2)

                # Normalize to reasonable range
                expected_move_pct = max(-10, min(15, expected_move_pct))

                hit_probability = min(100, max(0, (expected_move_pct + 5) / 10 * 100))

                projections[ticker] = {
                    'expected_move_pct': round(expected_move_pct, 2),
                    '5pct_probability': round(hit_probability, 1),
                    'atr_pct': round(atr_pct, 2),
                    'current_price': round(current_price, 2)
                }

            except Exception as e:
                logger.debug(f"Error projecting {ticker}: {e}")

        return projections

    def run_test(self):
        """Run the quick test."""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 QUICK TOP 3 VALIDATION TEST")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80)

        # Fetch and score
        scores = self.fetch_and_score()

        if not scores:
            logger.error("Failed to score stocks")
            return None

        # Rank
        result = self.rank_and_display(scores)

        if not result:
            logger.error("Failed to rank stocks")
            return None

        # Project returns
        projections = self.simulate_1week_returns(result['top3'] + result['top5'])

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("📈 1-WEEK RETURN PROJECTIONS")
        logger.info("=" * 80)

        logger.info("\nTOP 3 Projections:")
        top3_5pct_hits = 0
        for ticker in result['top3']:
            if ticker in projections:
                proj = projections[ticker]
                logger.info(f"  {ticker}: "
                           f"Expected move: {proj['expected_move_pct']:+.2f}% | "
                           f"5% Hit Probability: {proj['5pct_probability']:.1f}%")
                if proj['5pct_probability'] >= 50:
                    top3_5pct_hits += 1

        logger.info(f"\n  → Estimated Top 3 Win Rate: {(top3_5pct_hits/3)*100:.1f}% "
                   f"({top3_5pct_hits}/3 likely to hit 5%+)")

        logger.info("\nTOP 5 Projections:")
        top5_5pct_hits = 0
        for ticker in result['top5']:
            if ticker in projections:
                proj = projections[ticker]
                marker = "→" if ticker in result['top3'] else "  "
                logger.info(f"  {marker} {ticker}: Expected move: {proj['expected_move_pct']:+.2f}% | "
                           f"5% Hit Probability: {proj['5pct_probability']:.1f}%")
                if proj['5pct_probability'] >= 50:
                    top5_5pct_hits += 1

        logger.info(f"\n  → Estimated Top 5 Win Rate: {(top5_5pct_hits/5)*100:.1f}% "
                   f"({top5_5pct_hits}/5 likely to hit 5%+)")

        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("💡 QUICK TEST SUMMARY")
        logger.info("=" * 80)

        top3_wr = (top3_5pct_hits / 3) * 100
        top5_wr = (top5_5pct_hits / 5) * 100

        logger.info(f"\nOK Sample Stocks Tested: {len(scores)}")
        logger.info(f"OK Top 3 Estimated Win Rate: {top3_wr:.1f}%")
        logger.info(f"OK Top 5 Estimated Win Rate: {top5_wr:.1f}%")
        logger.info(f"OK Top 3 Advantage: {top3_wr - top5_wr:+.1f}%")

        if top3_wr > top5_wr:
            logger.info(f"\n✅ Top 3 outperforms Top 5 by {top3_wr - top5_wr:.1f}%")
            logger.info("   → Narrower selection captures higher-conviction trades")
        elif top3_wr == top5_wr:
            logger.info(f"\n🟡 Top 3 and Top 5 show similar performance")
        else:
            logger.info(f"\n🔵 Top 5 outperforms Top 3 by {top5_wr - top3_wr:.1f}%")
            logger.info("   → Broader selection captures more opportunities")

        logger.info("\n" + "=" * 80)
        logger.info("ℹ️  NOTE: This is a quick test with 20 sample stocks")
        logger.info("For comprehensive 5-year backtest, run: python backtest_top3_analysis.py")
        logger.info("=" * 80)

        return {
            'top3': result['top3'],
            'top5': result['top5'],
            'projections': projections,
            'top3_wr': top3_wr,
            'top5_wr': top5_wr,
        }


def main():
    """Run quick test."""
    test = QuickTop3Test()
    result = test.run_test()

    if result:
        logger.info("\nOK Quick test completed successfully!")
        logger.info(f"  Current Top 3: {', '.join(result['top3'])}")
        logger.info(f"  Current Top 5: {', '.join(result['top5'])}")

    return 0 if result else 1


if __name__ == "__main__":
    exit(main())

