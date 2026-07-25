"""Fibonacci Retracement analysis."""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FibonacciAnalysis:
    """Calculate Fibonacci retracement levels."""

    # Standard Fibonacci ratios
    LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    LEVEL_NAMES = {
        0.0: "Start",
        0.236: "23.6%",
        0.382: "38.2%",
        0.5: "50%",
        0.618: "61.8%",
        0.786: "78.6%",
        1.0: "100%",
    }

    @staticmethod
    def find_swing_high(df: pd.DataFrame, column: str = 'High', lookback: int = 20) -> Optional[Tuple[int, float]]:
        """
        Find recent swing high (local maximum).

        Args:
            df: OHLCV DataFrame
            column: Column to find high in
            lookback: Lookback period

        Returns:
            Tuple of (index, price) or None
        """
        if len(df) < lookback:
            return None

        recent = df[column].iloc[-lookback:]
        max_idx = recent.idxmax()
        max_price = recent.max()

        return (df.index.get_loc(max_idx), max_price)

    @staticmethod
    def find_swing_low(df: pd.DataFrame, column: str = 'Low', lookback: int = 20) -> Optional[Tuple[int, float]]:
        """
        Find recent swing low (local minimum).

        Args:
            df: OHLCV DataFrame
            column: Column to find low in
            lookback: Lookback period

        Returns:
            Tuple of (index, price) or None
        """
        if len(df) < lookback:
            return None

        recent = df[column].iloc[-lookback:]
        min_idx = recent.idxmin()
        min_price = recent.min()

        return (df.index.get_loc(min_idx), min_price)

    @staticmethod
    def calculate_uptrend_retracement(high_price: float, low_price: float) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels for uptrend (from low to high).

        Args:
            high_price: Swing high price
            low_price: Swing low price

        Returns:
            Dictionary {level_name: price}
        """
        if high_price <= low_price:
            logger.warning(f"Invalid prices for uptrend retracement: high={high_price}, low={low_price}")
            return {}

        diff = high_price - low_price
        levels = {}

        for ratio, name in FibonacciAnalysis.LEVEL_NAMES.items():
            price = high_price - (diff * ratio)
            levels[name] = round(price, 2)

        return levels

    @staticmethod
    def calculate_downtrend_retracement(high_price: float, low_price: float) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels for downtrend (from high to low).

        Args:
            high_price: Swing high price
            low_price: Swing low price

        Returns:
            Dictionary {level_name: price}
        """
        if high_price <= low_price:
            logger.warning(f"Invalid prices for downtrend retracement: high={high_price}, low={low_price}")
            return {}

        diff = high_price - low_price
        levels = {}

        for ratio, name in FibonacciAnalysis.LEVEL_NAMES.items():
            price = low_price + (diff * ratio)
            levels[name] = round(price, 2)

        return levels

    @staticmethod
    def get_nearest_levels(current_price: float, levels: Dict[str, float], num_levels: int = 3) -> List[Tuple[str, float]]:
        """
        Get nearest Fibonacci levels to current price.

        Args:
            current_price: Current stock price
            levels: Dictionary of Fibonacci levels
            num_levels: Number of nearest levels to return

        Returns:
            List of (level_name, price) tuples, sorted by distance
        """
        distances = [(name, price, abs(current_price - price)) for name, price in levels.items()]
        distances.sort(key=lambda x: x[2])
        return [(name, price) for name, price, _ in distances[:num_levels]]

    @staticmethod
    def analyze_price_position(current_price: float, levels: Dict[str, float]) -> Dict:
        """
        Analyze current price position relative to Fibonacci levels.

        Args:
            current_price: Current stock price
            levels: Dictionary of Fibonacci levels

        Returns:
            Analysis dictionary with position info
        """
        sorted_levels = sorted(levels.items(), key=lambda x: x[1])

        below_levels = [name for name, price in sorted_levels if price < current_price]
        above_levels = [name for name, price in sorted_levels if price > current_price]

        return {
            'current_price': current_price,
            'support_above': below_levels[-1] if below_levels else None,
            'resistance_below': above_levels[0] if above_levels else None,
            'nearest_support': sorted_levels[-1] if below_levels else sorted_levels[0],
            'nearest_resistance': sorted_levels[0] if above_levels else sorted_levels[-1],
        }

    @staticmethod
    def calculate_extended_levels(high_price: float, low_price: float, extension_level: float = 1.618) -> Dict[str, float]:
        """
        Calculate Fibonacci extension levels (targets beyond the swing high/low).

        Args:
            high_price: Swing high price
            low_price: Swing low price
            extension_level: Extension multiple (1.618 is golden ratio)

        Returns:
            Dictionary of extension levels
        """
        diff = high_price - low_price
        extension = high_price + (diff * (extension_level - 1))

        return {
            '161.8% Extension': round(extension, 2),
            '200% Extension': round(high_price + (diff * 2), 2),
            '261.8% Extension': round(high_price + (diff * 2.618), 2),
        }


def analyze_fibonacci(df: pd.DataFrame, recent_lookback: int = 60) -> Dict:
    """
    Complete Fibonacci analysis for a stock.

    Args:
        df: OHLCV DataFrame
        recent_lookback: Lookback period for finding swings

    Returns:
        Dictionary with Fibonacci analysis results
    """
    if len(df) < recent_lookback:
        return {}

    # Find swings
    swing_high = FibonacciAnalysis.find_swing_high(df, lookback=recent_lookback)
    swing_low = FibonacciAnalysis.find_swing_low(df, lookback=recent_lookback)

    if not swing_high or not swing_low:
        return {}

    high_idx, high_price = swing_high
    low_idx, low_price = swing_low

    current_price = df['Close'].iloc[-1]

    # Determine trend (Improved: now returns trend info)
    if high_idx > low_idx:  # High is more recent (downtrend)
        levels = FibonacciAnalysis.calculate_downtrend_retracement(high_price, low_price)
        trend = 'downtrend'
    else:  # Low is more recent (uptrend)
        levels = FibonacciAnalysis.calculate_uptrend_retracement(high_price, low_price)
        trend = 'uptrend'

    # Calculate extension levels (NEW: for future use)
    extensions = FibonacciAnalysis.calculate_extended_levels(high_price, low_price)

    return {
        'current_price': round(current_price, 2),
        'swing_high': round(high_price, 2),
        'swing_low': round(low_price, 2),
        'trend': trend,  # NEW: trend direction
        'retracement_levels': levels,
        'extension_levels': extensions,  # NEW: extension levels
        'nearest_levels': FibonacciAnalysis.get_nearest_levels(current_price, levels, num_levels=3),
        'position_analysis': FibonacciAnalysis.analyze_price_position(current_price, levels),
    }
