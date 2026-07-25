"""Beta (market sensitivity) calculation."""

import logging
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def calculate_beta(
    stock_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    lookback_days: int = 20
) -> Optional[float]:
    """
    Calculate Beta (market sensitivity) using covariance/variance formula.
    Beta = Cov(stock_returns, benchmark_returns) / Var(benchmark_returns)

    Args:
        stock_df: Stock OHLCV DataFrame with 'Close' column
        benchmark_df: Benchmark (SPY) OHLCV DataFrame with 'Close' column
        lookback_days: Number of days to look back (default 20)

    Returns:
        Beta value (float), or None if insufficient data
    """
    try:
        if len(stock_df) < 2 or len(benchmark_df) < 2:
            logger.warning("Insufficient data for beta calculation")
            return None

        # Get price columns
        stock_prices = stock_df['Close'].tail(lookback_days + 1)
        bench_prices = benchmark_df['Close'].tail(lookback_days + 1)

        # Calculate returns
        stock_returns = stock_prices.pct_change().dropna()
        bench_returns = bench_prices.pct_change().dropna()

        # Ensure overlapping date indices
        common_idx = stock_returns.index.intersection(bench_returns.index)

        if len(common_idx) < 2:
            logger.warning("Not enough overlapping data points for beta calculation")
            return None

        stock_returns = stock_returns.loc[common_idx]
        bench_returns = bench_returns.loc[common_idx]

        # Calculate covariance and variance
        covariance = np.cov(stock_returns, bench_returns)[0, 1]
        bench_variance = np.var(bench_returns, ddof=1)

        if abs(bench_variance) < 1e-10:
            logger.warning("Benchmark variance too close to zero for beta calculation")
            return None

        beta = covariance / bench_variance

        return round(float(beta), 3)

    except Exception as e:
        logger.error(f"Error calculating beta: {e}")
        return None
