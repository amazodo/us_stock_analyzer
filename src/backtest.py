"""Backtesting system for strategy validation."""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.collectors.stock_data import StockDataCollector
from src.collectors.ticker_manager import get_ticker_manager
from src.analysis.technical_score import TechnicalScoreCalculator
from src.recommender.ranker import StockRanker

logger = logging.getLogger(__name__)


class BacktestResult:
    """Single backtest result."""

    def __init__(
        self,
        test_date: str,
        recommended_top5: List[str],
        prices_at_rec: Dict[str, float],
        prices_1week_later: Dict[str, float],
        actual_gains: Dict[str, float]
    ):
        self.test_date = test_date
        self.recommended_top5 = recommended_top5
        self.prices_at_rec = prices_at_rec
        self.prices_1week_later = prices_1week_later
        self.actual_gains = actual_gains

        # Calculate accuracy metrics
        self.target_gains = {ticker: 5.0 for ticker in recommended_top5}
        self.hit_count = sum(1 for ticker in recommended_top5 if actual_gains.get(ticker, 0) >= 5.0)
        self.avg_gain = np.mean([actual_gains.get(ticker, 0) for ticker in recommended_top5])
        self.win_rate = (self.hit_count / len(recommended_top5)) if recommended_top5 else 0.0

    def to_dict(self) -> Dict:
        return {
            'test_date': self.test_date,
            'recommended_top5': self.recommended_top5,
            'hit_count': self.hit_count,
            'win_rate': round(self.win_rate * 100, 1),
            'avg_gain_pct': round(self.avg_gain, 2),
            'actual_gains': {k: round(v, 2) for k, v in self.actual_gains.items()},
        }


class Backtester:
    """Backtest strategy on historical data."""

    def __init__(self, years: int = 5, lookback_days: int = 365):
        self.years = years
        self.lookback_days = lookback_days
        self.stock_collector = StockDataCollector()
        self.ticker_manager = get_ticker_manager()
        self.technical_calculator = TechnicalScoreCalculator()
        self.ranker = StockRanker()

    def get_test_dates(self) -> List[datetime]:
        """
        Generate weekly test dates for the past N years.
        Tests on every Friday.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * self.years)

        test_dates = []
        current = start_date

        while current <= end_date:
            # Test on Fridays (weekday = 4)
            if current.weekday() == 4:
                test_dates.append(current)
            current += timedelta(days=1)

        # Limit to every 4 weeks (1 test per month)
        test_dates = test_dates[::4]

        logger.info(f"Generated {len(test_dates)} test dates over {self.years} years")
        return test_dates

    def get_historical_data_at_date(
        self,
        ticker: str,
        test_date: datetime,
        lookback_days: int
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data up to a specific date.
        Simulates having only data available at that point in time.
        """
        try:
            # Fetch longer period and filter to test_date
            total_days = lookback_days + 365  # Extra buffer
            end_date = test_date + timedelta(days=1)
            start_date = test_date - timedelta(days=total_days)

            stock = self.stock_collector.stock_collector.get_historical_data(
                ticker,
                period_days=total_days
            )

            if stock is None:
                return None

            # Filter to dates up to test_date
            stock = stock[stock.index.date <= test_date.date()]

            if len(stock) < 20:
                return None

            return stock.tail(lookback_days)

        except Exception as e:
            logger.debug(f"Error getting historical data for {ticker} at {test_date}: {e}")
            return None

    def simulate_top5_selection(
        self,
        test_date: datetime,
        tickers: List[str],
        lookback_days: int = 365
    ) -> Optional[Tuple[List[str], Dict[str, float]]]:
        """
        Simulate strategy for selecting top 5 at a specific test date.
        """
        try:
            scores = []

            for ticker in tickers:
                # Get data up to test_date
                df = self.get_historical_data_at_date(ticker, test_date, lookback_days)

                if df is None or len(df) < 20:
                    continue

                try:
                    # Calculate technical score (sentiment excluded for backtest)
                    tech_score, _ = self.technical_calculator.calculate_overall_technical_score(df)

                    # Use technical score for ranking (no sentiment in backtest)
                    scores.append((ticker, tech_score, 50.0))  # 50 = neutral sentiment

                except Exception as e:
                    logger.debug(f"Error scoring {ticker}: {e}")
                    continue

            if len(scores) < 5:
                logger.warning(f"Insufficient data at {test_date.date()}: only {len(scores)} tickers")
                return None

            # Rank and get top 5
            ranked = self.ranker.rank_stocks(scores)
            top5 = [s.ticker for s in ranked[:5]]

            # Get prices at test_date
            prices = {}
            for ticker in top5:
                df = self.get_historical_data_at_date(ticker, test_date, lookback_days)
                if df is not None and len(df) > 0:
                    prices[ticker] = float(df['Close'].iloc[-1])

            return top5, prices

        except Exception as e:
            logger.error(f"Error simulating top5 at {test_date}: {e}")
            return None

    def get_prices_at_date(
        self,
        tickers: List[str],
        target_date: datetime
    ) -> Dict[str, float]:
        """Get closing prices for tickers at a specific date."""
        prices = {}

        for ticker in tickers:
            try:
                # Fetch with buffer
                df = self.stock_collector.get_historical_data(
                    ticker,
                    period_days=365 * self.years
                )

                if df is None:
                    continue

                # Find closest date
                df_filtered = df[df.index.date <= target_date.date()]

                if len(df_filtered) > 0:
                    prices[ticker] = float(df_filtered['Close'].iloc[-1])

            except Exception as e:
                logger.debug(f"Error getting price for {ticker} at {target_date}: {e}")

        return prices

    def calculate_returns(
        self,
        top5: List[str],
        prices_at_rec: Dict[str, float],
        prices_1week_later: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate actual returns for recommended stocks."""
        returns = {}

        for ticker in top5:
            if ticker in prices_at_rec and ticker in prices_1week_later:
                start_price = prices_at_rec[ticker]
                end_price = prices_1week_later[ticker]

                if start_price > 0:
                    return_pct = ((end_price - start_price) / start_price) * 100
                    returns[ticker] = return_pct

        return returns

    def backtest(self) -> Dict:
        """Run full backtest."""
        logger.info("=" * 70)
        logger.info(f"Starting Backtest: {self.years} years, lookback {self.lookback_days} days")
        logger.info("=" * 70)

        # Get tickers
        tickers = self.ticker_manager.get_unified_universe()
        logger.info(f"Testing with {len(tickers)} tickers")

        # Get test dates
        test_dates = self.get_test_dates()

        # Run simulations
        results = []
        successful_tests = 0

        for i, test_date in enumerate(test_dates):
            logger.info(f"[{i+1}/{len(test_dates)}] Testing {test_date.date()}...")

            # Simulate top5 selection
            simulation = self.simulate_top5_selection(test_date, tickers, self.lookback_days)

            if simulation is None:
                continue

            top5, prices_at_rec = simulation

            # Get prices 1 week later
            prices_1week = self.get_prices_at_date(top5, test_date + timedelta(days=7))

            # Calculate returns
            actual_gains = self.calculate_returns(top5, prices_at_rec, prices_1week)

            # Create result
            result = BacktestResult(
                test_date=test_date.strftime("%Y-%m-%d"),
                recommended_top5=top5,
                prices_at_rec=prices_at_rec,
                prices_1week_later=prices_1week,
                actual_gains=actual_gains
            )

            results.append(result)
            successful_tests += 1

        # Calculate aggregate statistics
        logger.info("=" * 70)
        logger.info(f"OK Completed {successful_tests}/{len(test_dates)} tests")
        logger.info("=" * 70)

        if not results:
            logger.error("No successful backtest results")
            return {'error': 'No results'}

        # Aggregate metrics
        all_hit_counts = [r.hit_count for r in results]
        all_win_rates = [r.win_rate for r in results]
        all_avg_gains = [r.avg_gain for r in results]

        summary = {
            'backtest_period_years': self.years,
            'lookback_days': self.lookback_days,
            'total_tests': len(test_dates),
            'successful_tests': successful_tests,
            'success_rate': round((successful_tests / len(test_dates)) * 100, 1),
            'aggregate_metrics': {
                'avg_hit_count': round(np.mean(all_hit_counts), 1),
                'avg_win_rate_pct': round(np.mean(all_win_rates) * 100, 1),
                'median_win_rate_pct': round(np.median(all_win_rates) * 100, 1),
                'avg_gain_pct': round(np.mean(all_avg_gains), 2),
                'median_gain_pct': round(np.median(all_avg_gains), 2),
                'best_test_gain': round(max(all_avg_gains), 2),
                'worst_test_gain': round(min(all_avg_gains), 2),
            },
            'detailed_results': [r.to_dict() for r in results],
        }

        return summary


def run_backtest(years: int = 5, lookback_days: int = 365) -> Dict:
    """Convenience function to run backtest."""
    backtester = Backtester(years=years, lookback_days=lookback_days)
    return backtester.backtest()

