"""Run backtest and generate performance report."""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from config.settings import LOG_LEVEL, LOG_FILE, LOGS_DIR, OUTPUT_DIR
from src.backtest import run_backtest

# Setup logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def generate_backtest_report(backtest_results: dict) -> str:
    """Generate markdown report from backtest results."""

    md = "# 📊 Strategy Backtest Report\n\n"
    md += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    # Summary section
    md += "## 📈 Summary\n\n"
    md += f"- **Backtest Period**: {backtest_results.get('backtest_period_years', 5)} years\n"
    md += f"- **Lookback Period**: {backtest_results.get('lookback_days', 365)} days\n"
    md += f"- **Tests Conducted**: {backtest_results.get('successful_tests', 0)}/{backtest_results.get('total_tests', 0)}\n"
    md += f"- **Success Rate**: {backtest_results.get('success_rate', 0)}%\n\n"

    # Performance metrics
    metrics = backtest_results.get('aggregate_metrics', {})
    md += "## 🎯 Performance Metrics\n\n"
    md += f"### Win Rate (5% Gain Target)\n"
    md += f"- **Average Win Rate**: {metrics.get('avg_win_rate_pct', 0)}%\n"
    md += f"- **Median Win Rate**: {metrics.get('median_win_rate_pct', 0)}%\n"
    md += f"- **Average Hit Count**: {metrics.get('avg_hit_count', 0)}/5 stocks\n\n"

    md += f"### Actual Gains (1 Week)\n"
    md += f"- **Average Gain**: {metrics.get('avg_gain_pct', 0)}%\n"
    md += f"- **Median Gain**: {metrics.get('median_gain_pct', 0)}%\n"
    md += f"- **Best Performance**: {metrics.get('best_test_gain', 0)}%\n"
    md += f"- **Worst Performance**: {metrics.get('worst_test_gain', 0)}%\n\n"

    # Detailed results (last 20)
    detailed = backtest_results.get('detailed_results', [])
    if detailed:
        md += "## 📋 Recent Test Results (Last 20)\n\n"
        md += "| Date | Top 5 | Hits | Win Rate | Avg Gain |\n"
        md += "|------|-------|------|----------|----------|\n"

        for result in detailed[-20:]:
            date = result.get('test_date', 'N/A')
            tickers = ', '.join(result.get('recommended_top5', [])[:5])
            hits = result.get('hit_count', 0)
            win_rate = result.get('win_rate', 0)
            avg_gain = result.get('avg_gain_pct', 0)

            md += f"| {date} | {tickers} | {hits}/5 | {win_rate}% | {avg_gain}% |\n"

        md += "\n"

    # Interpretation
    md += "## 💡 Interpretation\n\n"

    avg_win_rate = metrics.get('avg_win_rate_pct', 0)
    avg_gain = metrics.get('avg_gain_pct', 0)

    md += "**Strategy Performance Summary**:\n\n"

    if avg_win_rate >= 60:
        md += f"✅ **Excellent**: Win rate of {avg_win_rate}% indicates strong predictive signal. "
        md += "The technical + sentiment scoring identifies high-quality opportunities.\n\n"
    elif avg_win_rate >= 40:
        md += f"⚠️ **Moderate**: Win rate of {avg_win_rate}% shows the strategy captures market moves better than random. "
        md += "Room for optimization in weighting or filtering.\n\n"
    else:
        md += f"❌ **Weak**: Win rate of {avg_win_rate}% suggests strategy needs refinement. "
        md += "Consider adjusting technical indicators or sentiment analysis.\n\n"

    if avg_gain >= 5:
        md += f"**Gain Achievement**: Average gain of {avg_gain}% meets/exceeds 5% weekly target.\n\n"
    else:
        md += f"**Gain Achievement**: Average gain of {avg_gain}% falls short of 5% target, but may still be profitable.\n\n"

    # Risks & Disclaimers
    md += "## ⚠️ Risks & Disclaimers\n\n"
    md += "- Past performance does NOT guarantee future results\n"
    md += "- Market conditions change; strategy may underperform in different regimes\n"
    md += "- Backtesting uses historical data with perfect foresight (no actual execution slippage)\n"
    md += "- Real trading involves fees, slippage, and timing issues not captured here\n"
    md += "- This is for educational purposes only; not investment advice\n\n"

    # Next steps
    md += "## 🚀 Next Steps\n\n"
    if avg_win_rate < 50:
        md += "1. **Optimize Weights**: Adjust technical indicator weights in `config/settings.py`\n"
        md += "2. **Improve Filtering**: Add volatility filters (ATR check for 5% feasibility)\n"
        md += "3. **Sentiment Tuning**: Refine sentiment analysis thresholds\n"
        md += "4. **Add Macro Filters**: Filter based on market regime (bullish/bearish)\n"
    else:
        md += "1. **Live Testing**: Deploy with small position sizes\n"
        md += "2. **Monitor Performance**: Track actual vs. backtest results\n"
        md += "3. **Continuous Optimization**: Adjust weights based on live performance\n"
        md += "4. **Risk Management**: Set stop losses and position sizing\n"

    md += "\n---\n"
    md += f"*Report generated: {datetime.now().isoformat()}*\n"

    return md


def main():
    """Run backtest and generate report."""
    parser = argparse.ArgumentParser(description="Run strategy backtest")
    parser.add_argument('--years', type=int, default=5, help='Number of years to backtest (default: 5)')
    parser.add_argument('--lookback', type=int, default=365, help='Lookback days for analysis (default: 365)')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("🔬 BACKTEST: Strategy Performance Validation")
    logger.info(f"Period: {args.years} years | Lookback: {args.lookback} days")
    logger.info("=" * 70)

    # Run backtest
    results = run_backtest(years=args.years, lookback_days=args.lookback)

    if 'error' in results:
        logger.error(f"Backtest failed: {results['error']}")
        return

    # Save JSON results
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    json_file = OUTPUT_DIR / f"backtest_results_{timestamp}.json"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"OK Results saved: {json_file}")

    # Generate and save markdown report
    md_content = generate_backtest_report(results)
    md_file = OUTPUT_DIR / f"backtest_report_{timestamp}.md"

    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    logger.info(f"OK Report saved: {md_file}")

    # Print summary to console
    metrics = results.get('aggregate_metrics', {})
    logger.info("\n" + "=" * 70)
    logger.info("📊 BACKTEST RESULTS SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Tests Completed: {results.get('successful_tests', 0)}/{results.get('total_tests', 0)}")
    logger.info(f"Win Rate (5% Target): {metrics.get('avg_win_rate_pct', 0)}%")
    logger.info(f"Average Gain (1 Week): {metrics.get('avg_gain_pct', 0)}%")
    logger.info(f"Best Performance: {metrics.get('best_test_gain', 0)}%")
    logger.info(f"Worst Performance: {metrics.get('worst_test_gain', 0)}%")
    logger.info("=" * 70)

    # Print recommendation
    avg_win_rate = metrics.get('avg_win_rate_pct', 0)
    if avg_win_rate >= 60:
        logger.info("✅ RESULT: Strategy shows STRONG predictive power (>60% win rate)")
    elif avg_win_rate >= 40:
        logger.info("⚠️  RESULT: Strategy shows MODERATE predictive power (40-60% win rate)")
    else:
        logger.info("❌ RESULT: Strategy needs OPTIMIZATION (<40% win rate)")

    logger.info("=" * 70)


if __name__ == "__main__":
    main()

