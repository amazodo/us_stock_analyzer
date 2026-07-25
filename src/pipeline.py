"""Main analysis pipeline orchestrator."""

import logging
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pandas as pd

from config.settings import (
    ANALYSIS_PERIOD_DAYS, MAX_WORKERS, MAX_RETRIES, RETRY_DELAY,
    MIN_MARKET_CAP, MIN_DAILY_VOLUME, ATR_FEASIBILITY_THRESHOLD_PCT,
    TARGET_GAIN_PERCENT, EARNINGS_RISK_WINDOW_DAYS, EARNINGS_RISK_PENALTY_POINTS,
    SECTOR_MOMENTUM_MAX_BONUS, SECTOR_MOMENTUM_LOOKBACK_DAYS, MARKET_REGIME_MA_PERIOD,
    VIX_TICKER
)
from src.collectors.stock_data import StockDataCollector
from src.collectors.news_data import NewsDataCollector
from src.collectors.ticker_manager import get_ticker_manager
from src.analysis.technical_score import TechnicalScoreCalculator
from src.analysis.sentiment_score import analyze_ticker_sentiment
from src.analysis.supply_demand import SupplyDemandAnalysis
from src.analysis.sector_momentum import calculate_sector_relative_strength
from src.analysis.market_regime import calculate_market_regime
from src.indicators.beta import calculate_beta
from src.recommender.ranker import rank_and_recommend, StockScore

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Complete stock analysis pipeline."""

    def __init__(self, period_days: int = ANALYSIS_PERIOD_DAYS):
        self.period_days = period_days
        self.stock_collector = StockDataCollector()
        self.news_collector = NewsDataCollector()
        self.ticker_manager = get_ticker_manager()
        self.technical_calculator = TechnicalScoreCalculator()

        logger.info(f"Pipeline initialized (analysis period: {period_days} days)")

    def fetch_stock_data(self, tickers: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical stock data for multiple tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary {ticker: DataFrame}
        """
        logger.info(f"Fetching stock data for {len(tickers)} tickers...")

        data = {}
        failed = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.stock_collector.get_historical_data, ticker, self.period_days): ticker
                for ticker in tickers
            }

            completed = 0
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    df = future.result()
                    if df is not None and len(df) > 0:
                        data[ticker] = df
                    else:
                        failed.append(ticker)
                except Exception as e:
                    logger.error(f"Error fetching {ticker}: {e}")
                    failed.append(ticker)

                completed += 1
                if completed % 20 == 0:
                    logger.info(f"Progress: {completed}/{len(tickers)}")

        logger.info(f"PASS Fetched data for {len(data)}/{len(tickers)} tickers")
        if failed:
            logger.warning(f"Failed to fetch: {len(failed)} tickers")

        return data

    def fetch_news_data(self, tickers: List[str]) -> Dict[str, List[Dict]]:
        """
        Fetch news articles for tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary {ticker: articles_list}
        """
        logger.info(f"Fetching news data for {len(tickers)} tickers...")

        news_data = {}

        with ThreadPoolExecutor(max_workers=max(2, MAX_WORKERS // 2)) as executor:
            futures = {
                executor.submit(self.news_collector.search_ticker_news, ticker, self.period_days): ticker
                for ticker in tickers
            }

            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    articles = future.result()
                    if articles:
                        news_data[ticker] = articles
                except Exception as e:
                    logger.error(f"Error fetching news for {ticker}: {e}")

        logger.info(f"PASS Fetched news for {len(news_data)}/{len(tickers)} tickers")

        return news_data

    def fetch_earnings_risk(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Fetch earnings risk data for multiple tickers using parallel processing.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary {ticker: {'within_risk_window': bool, 'next_earnings_date': date, 'days_until': int}}
        """
        logger.info(f"Fetching earnings risk data for {len(tickers)} tickers...")

        earnings_risk = {}
        failed = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.stock_collector.get_earnings_risk, ticker, EARNINGS_RISK_WINDOW_DAYS): ticker
                for ticker in tickers
            }

            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    risk_data = future.result()
                    if risk_data:
                        earnings_risk[ticker] = risk_data
                except Exception as e:
                    logger.debug(f"No earnings risk data for {ticker}: {e}")

        logger.info(f"PASS Fetched earnings risk for {len(earnings_risk)}/{len(tickers)} tickers")

        return earnings_risk

    def fetch_sector_map(self, tickers: List[str]) -> Dict[str, str]:
        """
        Fetch sector information for tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary {ticker: sector_name}
        """
        logger.info(f"Fetching sector data for {len(tickers)} tickers...")

        sector_map = {}

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.stock_collector.get_stock_info, ticker): ticker
                for ticker in tickers
            }

            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    info = future.result()
                    if info and 'sector' in info:
                        sector_map[ticker] = info['sector']
                    else:
                        sector_map[ticker] = 'Unknown'
                except Exception as e:
                    logger.debug(f"No sector data for {ticker}: {e}")
                    sector_map[ticker] = 'Unknown'

        logger.info(f"PASS Fetched sector data for {len(sector_map)}/{len(tickers)} tickers")

        return sector_map

    def fetch_benchmark_data(self, period_days: Optional[int] = None) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Fetch benchmark data (SPY, QQQ, VIX) for market regime calculation.

        Args:
            period_days: Number of days to fetch (uses self.period_days if None)

        Returns:
            Tuple of (spy_df, qqq_df, vix_df), or (None, None, None) if SPY fails
        """
        if period_days is None:
            period_days = self.period_days

        # Ensure we have enough data for moving average calculation
        benchmark_period = max(period_days, MARKET_REGIME_MA_PERIOD + SECTOR_MOMENTUM_LOOKBACK_DAYS + 5)

        try:
            spy_df = self.stock_collector.get_historical_data('SPY', benchmark_period)
            qqq_df = self.stock_collector.get_historical_data('QQQ', benchmark_period)
            vix_df = self.stock_collector.get_historical_data(VIX_TICKER, benchmark_period)

            if spy_df is not None and len(spy_df) > 0:
                logger.info(f"PASS Fetched benchmark data: SPY ({len(spy_df)} days), QQQ ({len(qqq_df) if qqq_df is not None else 0} days), VIX ({len(vix_df) if vix_df is not None else 0} days)")
                return spy_df, qqq_df, vix_df
            else:
                logger.warning("Failed to fetch benchmark data")
                return None, None, None
        except Exception as e:
            logger.error(f"Error fetching benchmark data: {e}")
            return None, None, None

    def calculate_technical_score(
        self,
        ticker: str,
        df: pd.DataFrame,
        beta: Optional[float] = None
    ) -> Tuple[float, Dict]:
        """
        Calculate technical score for a stock.

        Args:
            ticker: Stock ticker
            df: Historical price data
            beta: Market sensitivity coefficient (optional)

        Returns:
            Tuple of (overall_score, component_scores_dict)
        """
        try:
            score, components = self.technical_calculator.calculate_overall_technical_score(df, beta=beta)
            return score, components
        except Exception as e:
            logger.error(f"Error calculating technical score for {ticker}: {e}")
            return 50.0, {}

    def calculate_sentiment_score(self, ticker: str, articles: List[Dict]) -> float:
        """
        Calculate sentiment score for a stock.

        Args:
            ticker: Stock ticker
            articles: News articles

        Returns:
            Sentiment score (0-100)
        """
        try:
            if not articles:
                return 50.0  # Neutral if no news

            result = analyze_ticker_sentiment(ticker, articles, use_claude=False)
            return result.get('technical_score', 50.0)

        except Exception as e:
            logger.error(f"Error calculating sentiment for {ticker}: {e}")
            return 50.0

    def analyze_single_stock(
        self,
        ticker: str,
        stock_data: Optional[pd.DataFrame],
        news_articles: Optional[List[Dict]],
        benchmark_df: Optional[pd.DataFrame] = None
    ) -> Optional[Tuple[str, float, float]]:
        """
        Complete analysis for single stock.

        Args:
            ticker: Stock ticker
            stock_data: Price data
            news_articles: News articles
            benchmark_df: Benchmark (SPY) data for beta calculation

        Returns:
            Tuple of (ticker, technical_score, sentiment_score) or None
        """
        if stock_data is None or len(stock_data) < 20:
            logger.warning(f"{ticker}: Insufficient data")
            return None

        # Calculate beta if benchmark available
        beta = None
        if benchmark_df is not None and len(benchmark_df) > 0:
            beta = calculate_beta(stock_data, benchmark_df)

        # Technical score (with beta)
        tech_score, _ = self.calculate_technical_score(ticker, stock_data, beta=beta)

        # Sentiment score
        sentiment_score = self.calculate_sentiment_score(ticker, news_articles or [])

        return (ticker, tech_score, sentiment_score)

    def run_full_analysis(
        self,
        tickers: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> Dict:
        """
        Run complete analysis pipeline.

        Args:
            tickers: Specific tickers to analyze (None = use universe)
            use_cache: Whether to use cached data

        Returns:
            Analysis results dictionary
        """
        logger.info("=" * 60)
        logger.info("Starting Full Analysis Pipeline")
        logger.info(f"Period: {self.period_days} days | {datetime.now().isoformat()}")
        logger.info("=" * 60)

        # Get tickers
        if tickers is None:
            tickers = self.ticker_manager.get_unified_universe()
        logger.info(f"Analyzing {len(tickers)} tickers")

        # Step 1: Fetch data
        stock_data = self.fetch_stock_data(tickers)
        # Skip news data during analysis - fetch only for top5 after ranking
        news_data = {}
        earnings_risk_data = self.fetch_earnings_risk(tickers)

        # Step 1.1: Fetch sector and benchmark data
        sector_map = self.fetch_sector_map(tickers)
        spy_df, qqq_df, vix_df = self.fetch_benchmark_data()

        # Step 1.5: ATR filter - DISABLED for 30-day analysis (too strict)
        # For short periods (30 days), volatility filter would exclude most stocks
        # Re-enable for 180+ day analysis if needed
        logger.info("ATR volatility filter: DISABLED (use all stocks for 30-day analysis)")
        filtered_stock_data = stock_data  # Use all stock data without ATR filtering
        excluded_by_atr = []

        # Step 1.2: Calculate market regime
        market_regime = calculate_market_regime(spy_df, qqq_df, vix_df)

        # Step 2: Analyze each stock (using filtered stock data)
        logger.info("Calculating scores...")
        stock_scores = []

        for ticker, df in filtered_stock_data.items():
            articles = news_data.get(ticker, [])
            result = self.analyze_single_stock(ticker, df, articles, benchmark_df=spy_df)

            if result:
                stock_scores.append(result)

        logger.info(f"PASS Analyzed {len(stock_scores)} stocks with complete data")

        # Step 3: Calculate sector momentum bonuses
        sector_bonuses = {}
        if spy_df is not None and len(spy_df) > 0:
            logger.info("Calculating sector momentum...")
            sector_bonuses = calculate_sector_relative_strength(
                filtered_stock_data,
                sector_map,
                spy_df,
                lookback_days=SECTOR_MOMENTUM_LOOKBACK_DAYS,
                max_bonus=SECTOR_MOMENTUM_MAX_BONUS
            )
            logger.info(f"PASS Calculated sector bonuses for {len(sector_bonuses)} stocks")
        else:
            logger.warning("Benchmark data unavailable, skipping sector momentum")
            sector_bonuses = {ticker: 0.0 for ticker, _, _ in stock_scores}

        # Step 4: Prepare earnings penalties and flags
        earnings_penalties = {}
        earnings_flags = {}
        for ticker, tech, sent in stock_scores:
            risk_data = earnings_risk_data.get(ticker, {})
            if risk_data.get('within_risk_window', False):
                earnings_penalties[ticker] = EARNINGS_RISK_PENALTY_POINTS
                earnings_flags[ticker] = {
                    'warning': True,
                    'next_earnings_date': risk_data.get('next_earnings_date'),
                    'days_until': risk_data.get('days_until')
                }
            else:
                earnings_penalties[ticker] = 0.0

        # Step 5: Rank and recommend (Technical only)
        logger.info("Ranking stocks...")
        score_dict = {ticker: tech for ticker, tech, sent in stock_scores}

        # Normalize sector_bonuses: convert NaN to 0.0
        import math
        sector_bonuses_clean = {}
        for ticker, bonus in sector_bonuses.items():
            if isinstance(bonus, float) and math.isnan(bonus):
                sector_bonuses_clean[ticker] = 0.0
            else:
                sector_bonuses_clean[ticker] = bonus

        ranking_report = rank_and_recommend(
            score_dict,
            sector_bonuses=sector_bonuses_clean,
            earnings_penalties=earnings_penalties,
            earnings_flags=earnings_flags
        )

        # Step 4: Compile results
        results = {
            'timestamp': datetime.now().isoformat(),
            'period_days': self.period_days,
            'tickers_requested': len(tickers),
            'tickers_analyzed': len(stock_scores),
            'tickers_failed': len(tickers) - len(stock_scores) - len(excluded_by_atr),
            'tickers_excluded_by_atr': len(excluded_by_atr),
            'stock_scores': stock_scores,
            'ranking_report': ranking_report,
            'excluded_by_atr_filter': excluded_by_atr,
            'stock_data': stock_data,
            'news_data': news_data,
        }

        logger.info("=" * 60)
        logger.info("PASS Pipeline Complete")
        logger.info("=" * 60)

        results['earnings_risk_data'] = earnings_risk_data
        results['sector_map'] = sector_map
        results['sector_bonuses'] = sector_bonuses
        results['market_regime'] = market_regime

        return results


def run_analysis(
    tickers: Optional[List[str]] = None,
    period_days: int = ANALYSIS_PERIOD_DAYS
) -> Dict:
    """
    Convenience function to run analysis.

    Args:
        tickers: Specific tickers or None for full universe
        period_days: Analysis period in days

    Returns:
        Analysis results
    """
    pipeline = AnalysisPipeline(period_days=period_days)
    return pipeline.run_full_analysis(tickers=tickers)
