"""Momentum indicators: RSI, MACD, Stochastic."""

import logging
from typing import Tuple, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class MomentumIndicators:
    """Calculate momentum technical indicators."""

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, window: int = 14, column: str = 'Close') -> pd.DataFrame:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            df: OHLCV DataFrame
            window: RSI period (default: 14)
            column: Column to calculate RSI on

        Returns:
            DataFrame with RSI column added
        """
        df = df.copy()
        delta = df[column].diff()

        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        # Avoid division by zero
        rs = gain / loss.replace(0, 1e-10)
        df[f'RSI_{window}'] = 100 - (100 / (1 + rs))

        return df

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        column: str = 'Close'
    ) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            df: OHLCV DataFrame
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line EMA period (default: 9)
            column: Column to calculate MACD on

        Returns:
            DataFrame with MACD, Signal, Histogram columns
        """
        df = df.copy()

        # Calculate EMAs
        ema_fast = df[column].ewm(span=fast, adjust=False).mean()
        ema_slow = df[column].ewm(span=slow, adjust=False).mean()

        # MACD line
        df['MACD'] = ema_fast - ema_slow

        # Signal line
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()

        # Histogram
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        return df

    @staticmethod
    def calculate_stochastic(
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 1
    ) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator.

        Args:
            df: OHLCV DataFrame (must have High, Low, Close)
            k_period: K period (default: 14)
            d_period: D period (default: 3)
            smooth_k: Smoothing period for %K

        Returns:
            DataFrame with %K and %D columns
        """
        df = df.copy()

        # Lowest low and highest high over k_period
        low_min = df['Low'].rolling(window=k_period).min()
        high_max = df['High'].rolling(window=k_period).max()

        # Raw %K
        raw_k = 100 * (df['Close'] - low_min) / (high_max - low_min)

        # Smooth %K
        df['Stochastic_%K'] = raw_k.rolling(window=smooth_k).mean()

        # %D (SMA of %K)
        df['Stochastic_%D'] = df['Stochastic_%K'].rolling(window=d_period).mean()

        return df

    @staticmethod
    def get_rsi_signal(rsi_value: float, oversold: float = 30, overbought: float = 70) -> Optional[str]:
        """
        Get RSI signal (oversold, neutral, overbought).

        Args:
            rsi_value: Current RSI value
            oversold: Oversold threshold (default: 30)
            overbought: Overbought threshold (default: 70)

        Returns:
            'oversold', 'neutral', or 'overbought'
        """
        if pd.isna(rsi_value):
            return None

        if rsi_value < oversold:
            return 'oversold'
        elif rsi_value > overbought:
            return 'overbought'
        else:
            return 'neutral'

    @staticmethod
    def get_macd_signal(df: pd.DataFrame) -> Optional[str]:
        """
        Get MACD signal (buy, sell, neutral).

        Args:
            df: DataFrame with MACD, MACD_Signal, MACD_Histogram

        Returns:
            'buy', 'sell', or 'neutral'
        """
        if len(df) < 2:
            return None

        # Check if MACD columns exist
        if 'MACD' not in df.columns or 'MACD_Signal' not in df.columns:
            return None

        current_macd = df['MACD'].iloc[-1]
        current_signal = df['MACD_Signal'].iloc[-1]
        prev_macd = df['MACD'].iloc[-2]
        prev_signal = df['MACD_Signal'].iloc[-2]

        if pd.isna(current_macd) or pd.isna(current_signal):
            return None

        # Crossover signals
        if prev_macd <= prev_signal and current_macd > current_signal:
            return 'buy'
        elif prev_macd >= prev_signal and current_macd < current_signal:
            return 'sell'
        else:
            return 'neutral'

    @staticmethod
    def get_stochastic_signal(df: pd.DataFrame) -> Optional[str]:
        """
        Get Stochastic signal based on %K and %D.

        Args:
            df: DataFrame with Stochastic_%K and Stochastic_%D

        Returns:
            'oversold', 'overbought', 'neutral'
        """
        if len(df) < 1:
            return None

        if 'Stochastic_%K' not in df.columns:
            return None

        k_value = df['Stochastic_%K'].iloc[-1]

        if pd.isna(k_value):
            return None

        if k_value < 20:
            return 'oversold'
        elif k_value > 80:
            return 'overbought'
        else:
            return 'neutral'

    @staticmethod
    def calculate_momentum(df: pd.DataFrame, window: int = 10, column: str = 'Close') -> pd.DataFrame:
        """
        Calculate Price Momentum (Rate of Change).

        Args:
            df: OHLCV DataFrame
            window: Lookback period
            column: Column to calculate on

        Returns:
            DataFrame with Momentum column
        """
        df = df.copy()
        df[f'Momentum_{window}'] = df[column].pct_change(periods=window)
        return df


# Convenience functions
def rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Quick RSI calculation."""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Quick MACD calculation returns (MACD, Signal, Histogram)."""
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
