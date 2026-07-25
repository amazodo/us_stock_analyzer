"""Main entry point for US Stock AI Analyzer."""

import sys
import os
import io

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import argparse
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime

# Suppress yfinance warnings
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

from config.settings import (
    LOG_LEVEL, LOG_FILE, LOGS_DIR, CACHE_DIR, get_config_summary,
    TOP_N_RECOMMENDATIONS, ANALYSIS_PERIOD_DAYS
)
from src.pipeline import run_analysis
from src.recommender.report_generator import generate_weekly_report

# Setup logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="US Stock AI Analyzer - Top 5 Weekly Stock Recommendations"
    )

    parser.add_argument(
        '--tickers',
        nargs='+',
        help='Specific tickers to analyze (e.g., AAPL MSFT GOOGL)'
    )

    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report from cached data without re-fetching'
    )

    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear all cached data before running'
    )

    parser.add_argument(
        '--period-days',
        type=int,
        default=ANALYSIS_PERIOD_DAYS,
        help=f'Analysis period in days (default: {ANALYSIS_PERIOD_DAYS})'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with verbose output'
    )

    return parser


def load_cached_analysis(cache_file: Path) -> dict:
    """Load cached analysis results."""
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load cache: {e}")
        return None


def save_analysis_cache(results: dict, cache_file: Path):
    """Save analysis results to cache."""
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"OK Cached results to {cache_file}")
    except Exception as e:
        logger.error(f"Failed to cache results: {e}")


def main():
    """Main execution function."""
    parser = setup_argument_parser()
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("🚀 US Stock AI Analyzer - Weekly Top 5 Recommendations")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 70)

    # Print configuration
    logger.info(get_config_summary())

    # Clear cache if requested
    if args.clear_cache:
        logger.info("Clearing cache...")
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
            logger.info("OK Cache cleared")

    # Run analysis or load from cache
    today = datetime.now().strftime("%Y-%m-%d_%H%M")  # 시/분까지 표시
    cache_file = CACHE_DIR / f"analysis_cache_{today}.json"

    if args.report_only and cache_file.exists():
        logger.info("Loading cached analysis...")
        analysis_results = load_cached_analysis(cache_file)
        if not analysis_results:
            logger.error("Failed to load cache, running full analysis")
            analysis_results = run_analysis(tickers=args.tickers, period_days=args.period_days)
    else:
        logger.info("Running full analysis...")
        analysis_results = run_analysis(tickers=args.tickers, period_days=args.period_days)

        # Save cache
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        save_analysis_cache(analysis_results, cache_file)

    # Generate reports
    logger.info("Generating reports...")
    top_stocks = analysis_results.get('ranking_report', {}).get('recommendations', [])[:TOP_N_RECOMMENDATIONS]

    if not top_stocks:
        logger.warning("No recommendations generated")
        return

    # Fetch news only for top 5 stocks (after ranking)
    logger.info("Fetching news for top 5 stocks...")
    from src.collectors.news_data import NewsDataCollector
    news_collector = NewsDataCollector()
    top_tickers = [stock.get('ticker') for stock in top_stocks]
    news_data = {}
    for ticker in top_tickers:
        articles = news_collector.search_ticker_news(ticker, period_days=30)
        if articles:
            news_data[ticker] = articles
    logger.info(f"OK Fetched news for {len(news_data)}/{len(top_tickers)} top stocks")

    report_paths = generate_weekly_report(
        top_stocks=top_stocks,
        ranking_report=analysis_results.get('ranking_report', {}),
        news_data=news_data
    )

    logger.info("=" * 70)
    logger.info("OK Analysis Complete!")
    logger.info("=" * 70)

    # Print top 5
    logger.info("\n📊 TOP 5 RECOMMENDATIONS:\n")
    for rank, stock in enumerate(top_stocks, 1):
        ticker = stock.get('ticker', 'N/A')
        score = stock.get('overall_score', 0)
        tech = stock.get('technical_score', 0)

        logger.info(f"#{rank}. {ticker:8} | Overall Score: {score:6.1f}/100 | Technical: {tech:6.1f}/100")

    logger.info(f"\n📄 Reports saved to: {report_paths.get('markdown_report', 'N/A')}")

    logger.info("=" * 70)


if __name__ == "__main__":
    main()

