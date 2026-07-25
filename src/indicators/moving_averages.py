"""Moving average indicators: SMA, EMA, VWAP."""

import logging
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class MovingAverageIndicators:
    """Calculate moving average technical indicators."""

    @staticmethod
    def calculate_sma(df: pd.DataFrame, window: int = 20, column: str = 'Close') -> pd.DataFrame:
        """
        Calculate Simple Moving Average (SMA).

        Args:
            df: OHLCV DataFrame
            window: Period for SMA
            column: Column to calculate SMA on (default: Close)

        Returns:
            DataFrame with SMA_{window} column added
        """
        df = df.copy()
        df[f'SMA_{window}'] = df[column].rolling(window=window).mean()
        return df

    @staticmethod
    def calculate_ema(df: pd.DataFrame, window: int = 20, column: str = 'Close') -> pd.DataFrame:
        """
        Calculate Exponential Moving Average (EMA).

        Args:
            df: OHLCV DataFrame
            window: Period for EMA
            column: Column to calculate EMA on

        Returns:
            DataFrame with EMA_{window} column added
        """
        df = df.copy()
        df[f'EMA_{window}'] = df[column].ewm(span=window, adjust=False).mean()
        return df

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Volume Weighted Average Price (VWAP).

        Args:
            df: OHLCV DataFrame (must have High, Low, Close, Volume)

        Returns:
            DataFrame with VWAP column added
        """
        df = df.copy()

        # Typical Price = (High + Low + Close) / 3
        tp = (df['High'] + df['Low'] + df['Close']) / 3

        # Cumulative TP * Volume / Cumulative Volume
        df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

        return df

    @staticmethod
    def calculate_multiple_smas(
        df: pd.DataFrame,
        periods: list = [20, 50, 200],
        column: str = 'Close'
    ) -> pd.DataFrame:
        """
        Calculate multiple SMAs at once.

        Args:
            df: OHLCV DataFrame
            periods: List of periods for SMAs
            column: Column to calculate SMAs on

        Returns:
            DataFrame with all SMA columns added
        """
        df = df.copy()
        for period in periods:
            df[f'SMA_{period}'] = df[column].rolling(window=period).mean()
        return df

    @staticmethod
    def calculate_multiple_emas(
        df: pd.DataFrame,
        periods: list = [12, 26],
        column: str = 'Close'
    ) -> pd.DataFrame:
        """
        Calculate multiple EMAs at once.

        Args:
            df: OHLCV DataFrame
            periods: List of periods for EMAs
            column: Column to calculate EMAs on

        Returns:
            DataFrame with all EMA columns added
        """
        df = df.copy()
        for period in periods:
            df[f'EMA_{period}'] = df[column].ewm(span=period, adjust=False).mean()
        return df

    @staticmethod
    def get_trend_direction(
        df: pd.DataFrame,
        short_period: int = 20,
        long_period: int = 50,
        column: str = 'Close'
    ) -> Optional[str]:
        """
        Determine trend direction based on SMA crossover.

        Args:
            df: OHLCV DataFrame
            short_period: Short-term SMA period
            long_period: Long-term SMA period
            column: Column to base trend on

        Returns:
            'uptrend', 'downtrend', or None if insufficient data
        """
        if len(df) < long_period:
            return None

        df = df.copy()
        df[f'SMA_{short_period}'] = df[column].rolling(window=short_period).mean()
        df[f'SMA_{long_period}'] = df[column].rolling(window=long_period).mean()

        latest_short = df[f'SMA_{short_period}'].iloc[-1]
        latest_long = df[f'SMA_{long_period}'].iloc[-1]

        if pd.isna(latest_short) or pd.isna(latest_long):
            return None

        if latest_short > latest_long:
            return 'uptrend'
        elif latest_short < latest_long:
            return 'downtrend'
        else:
            return None

    @staticmethod
    def calculate_price_position(
        df: pd.DataFrame,
        window: int = 20,
        column: str = 'Close'
    ) -> Optional[float]:
        """
        Calculate where current price sits relative to SMA (0-1 scale).
        0 = at/below SMA, 1 = significantly above SMA.

        Args:
            df: OHLCV DataFrame
            window: SMA period
            column: Price column

        Returns:
            Position value (0-1) or None
        """
        if len(df) < window:
            return None

        df = df.copy()
        sma = df[column].rolling(window=window).mean().iloc[-1]
        current_price = df[column].iloc[-1]

        if pd.isna(sma):
            return None

        # Calculate standard deviation for normalization
        recent_prices = df[column].iloc[-window:]
        std_dev = recent_prices.std()

        if std_dev == 0:
            return 0.5 if current_price == sma else (1.0 if current_price > sma else 0.0)

        # Normalize to 0-1 range
        distance = (current_price - sma) / std_dev
        position = max(0, min(1, 0.5 + (distance / (2 * 2))))  # Normalize to 0-1

        return position


# Convenience functions
def sma(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Quick SMA calculation."""
    return df['Close'].rolling(window=window).mean()


def ema(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Quick EMA calculation."""
    return df['Close'].ewm(span=window, adjust=False).mean()


def vwap(df: pd.DataFrame) -> pd.Series:
    """Quick VWAP calculation."""
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    return (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
