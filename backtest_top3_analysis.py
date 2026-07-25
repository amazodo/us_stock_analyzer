"""Detailed backtest for Top 3 vs Top 5 comparison and validation."""

import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict

from config.settings import LOG_LEVEL, LOGS_DIR, OUTPUT_DIR
from src.collectors.stock_data import StockDataCollector
from src.collectors.ticker_manager import get_ticker_manager
from src.analysis.technical_score import TechnicalScoreCalculator
from src.recommender.ranker import StockRanker

# Setup logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "backtest_top3.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Top3Validator:
    """Detailed validation of Top 3 stock recommendations."""

    def __init__(self, years: int = 5, lookback_days: int = 365):
        self.years = years
        self.lookback_days = lookback_days
        self.stock_collector = StockDataCollector()
        self.ticker_manager = get_ticker_manager()
        self.technical_calculator = TechnicalScoreCalculator()
        self.ranker = StockRanker()

    def get_test_dates(self) -> List[datetime]:
        """Generate weekly test dates (Fridays)."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * self.years)

        test_dates = []
        current = start_date

        while current <= end_date:
            if current.weekday() == 4:  # Friday
                test_dates.append(current)
            current += timedelta(days=1)

        # Every 4 weeks
        test_dates = test_dates[::4]
        logger.info(f"Generated {len(test_dates)} test dates")
        return test_dates

    def get_historical_data_at_date(
        self,
        ticker: str,
        test_date: datetime,
        lookback_days: int
    ) -> pd.DataFrame:
        """Get data available at a specific point in time."""
        try:
            stock = self.stock_collector.get_historical_data(
                ticker,
                period_days=lookback_days + 365
            )

            if stock is None or len(stock) < 20:
                return None

            stock = stock[stock.index.date <= test_date.date()]

            if len(stock) < 20:
                return None

            return stock.tail(lookback_days)

        except Exception as e:
            logger.debug(f"Error for {ticker} at {test_date}: {e}")
            return None

    def simulate_top3_top5(
        self,
        test_date: datetime,
        tickers: List[str]
    ) -> Tuple[List[str], List[str], Dict[str, float]]:
        """
        Simulate top 3 and top 5 selection at a test date.

        Returns:
            (top3, top5, prices_dict)
        """
        try:
            scores = []

            for ticker in tickers:
                df = self.get_historical_data_at_date(ticker, test_date, self.lookback_days)

                if df is None or len(df) < 20:
                    continue

                try:
                    tech_score, _ = self.technical_calculator.calculate_overall_technical_score(df)
                    scores.append((ticker, tech_score, 50.0))  # Neutral sentiment
                except:
                    continue

            if len(scores) < 5:
                return None, None, None

            ranked = self.ranker.rank_stocks(scores)

            top3 = [s.ticker for s in ranked[:3]]
            top5 = [s.ticker for s in ranked[:5]]

            # Get prices
            prices = {}
            for ticker in top5:
                df = self.get_historical_data_at_date(ticker, test_date, self.lookback_days)
                if df is not None and len(df) > 0:
                    prices[ticker] = float(df['Close'].iloc[-1])

            return top3, top5, prices

        except Exception as e:
            logger.error(f"Error simulating at {test_date}: {e}")
            return None, None, None

    def get_prices_at_date(self, tickers: List[str], target_date: datetime) -> Dict[str, float]:
        """Get prices at a specific date."""
        prices = {}

        for ticker in tickers:
            try:
                df = self.stock_collector.get_historical_data(
                    ticker,
                    period_days=365 * self.years
                )

                if df is None:
                    continue

                df_filtered = df[df.index.date <= target_date.date()]

                if len(df_filtered) > 0:
                    prices[ticker] = float(df_filtered['Close'].iloc[-1])

            except Exception as e:
                logger.debug(f"Error for {ticker}: {e}")

        return prices

    def backtest(self) -> Dict:
        """Run detailed backtest."""
        logger.info("=" * 80)
        logger.info("🔬 TOP 3 vs TOP 5 BACKTEST ANALYSIS")
        logger.info(f"Period: {self.years} years | Lookback: {self.lookback_days} days")
        logger.info("=" * 80)

        tickers = self.ticker_manager.get_unified_universe()
        test_dates = self.get_test_dates()

        # Track results
        top3_results = []
        top5_results = []

        for i, test_date in enumerate(test_dates):
            logger.info(f"[{i+1}/{len(test_dates)}] {test_date.date()}")

            # Simulate
            top3, top5, prices = self.simulate_top3_top5(test_date, tickers)

            if top3 is None:
                continue

            # Get prices 1 week later
            prices_1week = self.get_prices_at_date(top5, test_date + timedelta(days=7))

            # Calculate returns
            top3_returns = self.calculate_returns(top3, prices, prices_1week)
            top5_returns = self.calculate_returns(top5, prices, prices_1week)

            # Hits (5% gain)
            top3_hits = sum(1 for r in top3_returns.values() if r >= 5.0)
            top5_hits = sum(1 for r in top5_returns.values() if r >= 5.0)

            # Stats
            top3_avg = np.mean(list(top3_returns.values())) if top3_returns else 0
            top5_avg = np.mean(list(top5_returns.values())) if top5_returns else 0

            top3_results.append({
                'date': test_date.strftime("%Y-%m-%d"),
                'tickers': top3,
                'returns': top3_returns,
                'hits': top3_hits,
                'avg_gain': round(top3_avg, 2),
                'win_rate': round((top3_hits / 3 * 100) if top3_returns else 0, 1)
            })

            top5_results.append({
                'date': test_date.strftime("%Y-%m-%d"),
                'tickers': top5,
                'returns': top5_returns,
                'hits': top5_hits,
                'avg_gain': round(top5_avg, 2),
                'win_rate': round((top5_hits / 5 * 100) if top5_returns else 0, 1)
            })

        logger.info("\n" + "=" * 80)
        logger.info(f"OK Completed {len(top3_results)} backtests")
        logger.info("=" * 80)

        return {
            'period_years': self.years,
            'total_tests': len(top3_results),
            'top3_results': top3_results,
            'top5_results': top5_results,
            'top3_aggregate': self.calculate_aggregate(top3_results, 3),
            'top5_aggregate': self.calculate_aggregate(top5_results, 5),
            'comparison': self.compare_top3_top5(top3_results, top5_results),
        }

    def calculate_returns(self, tickers: List[str], prices_start: Dict, prices_end: Dict) -> Dict[str, float]:
        """Calculate returns."""
        returns = {}
        for ticker in tickers:
            if ticker in prices_start and ticker in prices_end:
                start = prices_start[ticker]
                end = prices_end[ticker]
                if start > 0:
                    returns[ticker] = ((end - start) / start) * 100

        return returns

    def calculate_aggregate(self, results: List[Dict], top_n: int) -> Dict:
        """Calculate aggregate statistics."""
        if not results:
            return {}

        all_wins = [r['hits'] for r in results]
        all_win_rates = [r['win_rate'] for r in results]
        all_gains = [r['avg_gain'] for r in results]

        # All individual returns
        all_returns = []
        for r in results:
            all_returns.extend(r['returns'].values())

        return {
            'tests': len(results),
            'avg_hit_count': round(np.mean(all_wins), 2),
            'total_hits': sum(all_wins),
            'total_possible': len(results) * top_n,
            'overall_win_rate_pct': round((sum(all_wins) / (len(results) * top_n)) * 100, 2),
            'avg_win_rate_pct': round(np.mean(all_win_rates), 1),
            'median_win_rate_pct': round(np.median(all_win_rates), 1),
            'best_win_rate_pct': round(max(all_win_rates), 1) if all_win_rates else 0,
            'worst_win_rate_pct': round(min(all_win_rates), 1) if all_win_rates else 0,
            'avg_gain_pct': round(np.mean(all_gains), 2),
            'median_gain_pct': round(np.median(all_gains), 2),
            'best_gain_pct': round(max(all_gains), 2) if all_gains else 0,
            'worst_gain_pct': round(min(all_gains), 2) if all_gains else 0,
            'all_returns_mean': round(np.mean(all_returns), 2) if all_returns else 0,
            'all_returns_std': round(np.std(all_returns), 2) if all_returns else 0,
            'all_returns_min': round(min(all_returns), 2) if all_returns else 0,
            'all_returns_max': round(max(all_returns), 2) if all_returns else 0,
        }

    def compare_top3_top5(self, top3_results: List[Dict], top5_results: List[Dict]) -> Dict:
        """Compare Top 3 vs Top 5 performance."""
        top3_agg = self.calculate_aggregate(top3_results, 3)
        top5_agg = self.calculate_aggregate(top5_results, 5)

        return {
            'top3_overall_win_rate': top3_agg.get('overall_win_rate_pct', 0),
            'top5_overall_win_rate': top5_agg.get('overall_win_rate_pct', 0),
            'top3_vs_top5_win_rate_improvement': round(
                top3_agg.get('overall_win_rate_pct', 0) - top5_agg.get('overall_win_rate_pct', 0), 2
            ),
            'top3_avg_gain': top3_agg.get('avg_gain_pct', 0),
            'top5_avg_gain': top5_agg.get('avg_gain_pct', 0),
            'top3_vs_top5_gain_diff': round(
                top3_agg.get('avg_gain_pct', 0) - top5_agg.get('avg_gain_pct', 0), 2
            ),
            'top3_hit_ratio': f"{top3_agg.get('total_hits', 0)}/{top3_agg.get('total_possible', 0)}",
            'top5_hit_ratio': f"{top5_agg.get('total_hits', 0)}/{top5_agg.get('total_possible', 0)}",
        }


def generate_top3_report(results: Dict) -> str:
    """Generate markdown report."""
    md = "# 📊 Top 3 vs Top 5 Stock Recommendation Analysis\n\n"
    md += f"**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    md += f"**Backtest Period**: {results.get('period_years', 5)} years\n"
    md += f"**Tests Completed**: {results.get('total_tests', 0)}\n\n"

    # Summary comparison
    md += "## 🎯 Top 3 vs Top 5 Performance\n\n"
    comp = results.get('comparison', {})

    md += "| Metric | Top 3 | Top 5 | Difference |\n"
    md += "|--------|-------|-------|------------|\n"

    top3_wr = comp.get('top3_overall_win_rate', 0)
    top5_wr = comp.get('top5_overall_win_rate', 0)
    diff_wr = comp.get('top3_vs_top5_win_rate_improvement', 0)

    md += f"| **Win Rate (5% Target)** | {top3_wr}% | {top5_wr}% | **+{diff_wr}%** |\n"

    top3_gain = comp.get('top3_avg_gain', 0)
    top5_gain = comp.get('top5_avg_gain', 0)
    diff_gain = comp.get('top3_vs_top5_gain_diff', 0)

    md += f"| **Avg Weekly Gain** | {top3_gain}% | {top5_gain}% | **+{diff_gain}%** |\n"

    md += f"| **Hit Ratio** | {comp.get('top3_hit_ratio')} | {comp.get('top5_hit_ratio')} | |\n\n"

    # Top 3 detailed stats
    md += "## 🏆 Top 3 Detailed Statistics\n\n"
    top3 = results.get('top3_aggregate', {})

    md += f"### Win Rate Analysis\n"
    md += f"- **Overall Win Rate**: {top3.get('overall_win_rate_pct', 0)}%\n"
    md += f"  - Total Hits: {top3.get('total_hits', 0)} out of {top3.get('total_possible', 0)}\n"
    md += f"- **Average Win Rate**: {top3.get('avg_win_rate_pct', 0)}%\n"
    md += f"- **Median Win Rate**: {top3.get('median_win_rate_pct', 0)}%\n"
    md += f"- **Best Week**: {top3.get('best_win_rate_pct', 0)}%\n"
    md += f"- **Worst Week**: {top3.get('worst_win_rate_pct', 0)}%\n\n"

    md += f"### Return Analysis\n"
    md += f"- **Average Gain**: {top3.get('avg_gain_pct', 0)}%\n"
    md += f"- **Median Gain**: {top3.get('median_gain_pct', 0)}%\n"
    md += f"- **Best Gain**: {top3.get('best_gain_pct', 0)}%\n"
    md += f"- **Worst Gain**: {top3.get('worst_gain_pct', 0)}%\n"
    md += f"- **All Returns Mean**: {top3.get('all_returns_mean', 0)}%\n"
    md += f"- **All Returns Std Dev**: {top3.get('all_returns_std', 0)}%\n\n"

    # Top 5 stats for comparison
    md += "## 📊 Top 5 Statistics (for reference)\n\n"
    top5 = results.get('top5_aggregate', {})

    md += f"- **Overall Win Rate**: {top5.get('overall_win_rate_pct', 0)}%\n"
    md += f"  - Total Hits: {top5.get('total_hits', 0)} out of {top5.get('total_possible', 0)}\n"
    md += f"- **Average Gain**: {top5.get('avg_gain_pct', 0)}%\n"
    md += f"- **Median Gain**: {top5.get('median_gain_pct', 0)}%\n\n"

    # Key findings
    md += "## 🔍 Key Findings\n\n"

    if top3_wr > top5_wr:
        improvement = top3_wr - top5_wr
        md += f"✅ **Top 3 outperforms Top 5** by {improvement}% in win rate\n"
        md += f"   - Top 3 is more selective, capturing highest-conviction opportunities\n"
    else:
        md += f"⚠️ **Top 5 outperforms Top 3** (but only by {abs(diff_wr)}%)\n"

    if top3_gain >= 5.0:
        md += f"✅ **Top 3 achieves 5% target**: Average gain of {top3_gain}%\n"
    elif top3_gain >= 4.5:
        md += f"⚠️ **Top 3 nearly achieves target**: Average gain of {top3_gain}% (95%)\n"
    else:
        md += f"❌ **Top 3 falls short**: Average gain of {top3_gain}% (below 5% target)\n"

    md += f"📈 **Consistency**: Win rate {top3.get('avg_win_rate_pct', 0)}% (avg) with "
    md += f"std dev of {top3.get('all_returns_std', 0)}%\n"
    md += f"   - Lower std dev = more consistent results\n\n"

    # Recommendation
    md += "## 💡 Recommendation\n\n"

    if top3_wr >= 65:
        md += "🟢 **Use Top 3**: Excellent hit rate justifies narrower selection\n"
    elif top3_wr >= 55:
        md += "🟡 **Top 3 or Top 5**: Similar performance, choose based on risk tolerance\n"
        md += f"   - Higher conviction (Top 3): {top3_wr}% hit rate\n"
        md += f"   - Diversification (Top 5): {top5_wr}% hit rate\n"
    else:
        md += "🔵 **Prefer Top 5**: Broader selection captures more opportunities\n"

    md += "\n---\n"
    md += f"*Analysis generated: {datetime.now().isoformat()}*\n"

    return md


def main():
    """Run Top 3 analysis."""
    import json

    logger.info("Starting Top 3 validation backtest...")

    validator = Top3Validator(years=5, lookback_days=365)
    results = validator.backtest()

    # Save JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    json_file = OUTPUT_DIR / f"backtest_top3_analysis_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"OK JSON saved: {json_file}")

    # Generate report
    md_content = generate_top3_report(results)
    md_file = OUTPUT_DIR / f"backtest_top3_report_{timestamp}.md"

    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    logger.info(f"OK Report saved: {md_file}")

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 TOP 3 vs TOP 5 BACKTEST RESULTS")
    logger.info("=" * 80)

    comp = results.get('comparison', {})
    top3 = results.get('top3_aggregate', {})
    top5 = results.get('top5_aggregate', {})

    logger.info(f"\n🏆 TOP 3 PERFORMANCE:")
    logger.info(f"  Win Rate:     {comp.get('top3_overall_win_rate', 0)}%")
    logger.info(f"  Avg Gain:     {comp.get('top3_avg_gain', 0)}%")
    logger.info(f"  Hit Ratio:    {comp.get('top3_hit_ratio')}")
    logger.info(f"  Best Week:    {top3.get('best_gain_pct', 0)}%")
    logger.info(f"  Worst Week:   {top3.get('worst_gain_pct', 0)}%")

    logger.info(f"\n📊 TOP 5 PERFORMANCE:")
    logger.info(f"  Win Rate:     {comp.get('top5_overall_win_rate', 0)}%")
    logger.info(f"  Avg Gain:     {comp.get('top5_avg_gain', 0)}%")
    logger.info(f"  Hit Ratio:    {comp.get('top5_hit_ratio')}")
    logger.info(f"  Best Week:    {top5.get('best_gain_pct', 0)}%")
    logger.info(f"  Worst Week:   {top5.get('worst_gain_pct', 0)}%")

    logger.info(f"\n📈 COMPARISON:")
    logger.info(f"  Win Rate Improvement:  {comp.get('top3_vs_top5_win_rate_improvement', 0):+.2f}%")
    logger.info(f"  Gain Difference:       {comp.get('top3_vs_top5_gain_diff', 0):+.2f}%")

    logger.info("\n" + "=" * 80)

    # Interpretation
    top3_wr = comp.get('top3_overall_win_rate', 0)
    if top3_wr >= 65:
        logger.info("✅ RESULT: TOP 3 shows EXCELLENT hit rate - recommend using Top 3")
    elif top3_wr >= 55:
        logger.info("🟡 RESULT: TOP 3 performs well - choose based on risk tolerance")
    else:
        logger.info("🔵 RESULT: TOP 5 may be preferable for broader selection")

    logger.info("=" * 80)


if __name__ == "__main__":
    main()

