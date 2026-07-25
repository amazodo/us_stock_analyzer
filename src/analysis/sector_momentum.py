"""Sector relative strength and momentum analysis."""

import logging
from typing import Dict, Optional
import pandas as pd
import numpy as np

from config.settings import SECTOR_MOMENTUM_MAX_BONUS, SECTOR_MOMENTUM_LOOKBACK_DAYS

logger = logging.getLogger(__name__)


def calculate_sector_relative_strength(
    stock_data: Dict[str, pd.DataFrame],
    sector_map: Dict[str, str],
    benchmark_df: pd.DataFrame,
    lookback_days: int = SECTOR_MOMENTUM_LOOKBACK_DAYS,
    max_bonus: float = SECTOR_MOMENTUM_MAX_BONUS
) -> Dict[str, float]:
    """
    Calculate sector relative strength and derive momentum bonus for each ticker.

    Algorithm:
    1. For each sector, calculate average return of its member tickers over lookback_days
    2. Calculate benchmark (SPY) return over the same period
    3. Relative return = sector_return - benchmark_return (in percentage points)
    4. Bonus = clip(relative_return * 2, -max_bonus, +max_bonus)  # heuristic sensitivity factor

    Args:
        stock_data: Dict mapping ticker -> DataFrame with 'Close' column
        sector_map: Dict mapping ticker -> sector name
        benchmark_df: Benchmark (SPY) DataFrame with 'Close' column
        lookback_days: Number of days to look back (default 20)
        max_bonus: Maximum bonus/penalty in points (default 5.0)

    Returns:
        Dict mapping ticker -> momentum_bonus (float, -max_bonus to +max_bonus)
    """
    try:
        # Calculate benchmark return
        if len(benchmark_df) < 2:
            logger.warning("Insufficient benchmark data for sector momentum calculation")
            return {ticker: 0.0 for ticker in stock_data.keys()}

        bench_prices = benchmark_df['Close'].tail(lookback_days + 1)
        bench_return_pct = ((bench_prices.iloc[-1] - bench_prices.iloc[0]) / bench_prices.iloc[0]) * 100

        # Group tickers by sector and calculate sector returns
        sector_returns = {}
        sector_tickers = {}

        for ticker, df in stock_data.items():
            sector = sector_map.get(ticker, 'Unknown')

            if len(df) < 2:
                continue

            prices = df['Close'].tail(lookback_days + 1)
            ticker_return_pct = ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]) * 100

            if sector not in sector_returns:
                sector_returns[sector] = []
                sector_tickers[sector] = []

            sector_returns[sector].append(ticker_return_pct)
            sector_tickers[sector].append(ticker)

        # Calculate average return per sector
        sector_avg_returns = {
            sector: np.mean(returns)
            for sector, returns in sector_returns.items()
        }

        # Calculate bonuses: relative strength vs benchmark, scaled by 2x sensitivity factor
        bonuses = {}
        for ticker, df in stock_data.items():
            sector = sector_map.get(ticker, 'Unknown')

            if sector not in sector_avg_returns:
                bonuses[ticker] = 0.0
                continue

            sector_return = sector_avg_returns[sector]
            relative_return = sector_return - bench_return_pct

            # Heuristic: 2x sensitivity factor (can be tuned in config)
            raw_bonus = relative_return * 2.0

            # Clip to [-max_bonus, +max_bonus]
            bonus = np.clip(raw_bonus, -max_bonus, max_bonus)
            bonuses[ticker] = round(bonus, 2)

        return bonuses

    except Exception as e:
        logger.warning(f"Sector momentum calculation failed: {e}")
        return {ticker: 0.0 for ticker in stock_data.keys()}
