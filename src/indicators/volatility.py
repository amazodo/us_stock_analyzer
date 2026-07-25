"""Volatility indicators: Bollinger Bands, ATR."""

import logging
from typing import Tuple, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class VolatilityIndicators:
    """Calculate volatility technical indicators."""

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        window: int = 20,
        num_std: float = 2.0,
        column: str = 'Close'
    ) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.

        Args:
            df: OHLCV DataFrame
            window: SMA period (default: 20)
            num_std: Number of standard deviations (default: 2.0)
            column: Column to calculate on

        Returns:
            DataFrame with BB_Upper, BB_Middle, BB_Lower columns
        """
        df = df.copy()

        # Middle band (SMA)
        middle = df[column].rolling(window=window).mean()
        std = df[column].rolling(window=window).std()

        # Upper and lower bands
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)

        df['BB_Upper'] = upper
        df['BB_Middle'] = middle
        df['BB_Lower'] = lower

        # Bollinger Band Width and Position
        df['BB_Width'] = upper - lower
        df['BB_Position'] = (df[column] - lower) / (upper - lower)

        return df

    @staticmethod
    def calculate_atr(
        df: pd.DataFrame,
        window: int = 14
    ) -> pd.DataFrame:
        """
        Calculate Average True Range (ATR).

        Args:
            df: OHLCV DataFrame (must have High, Low, Close)
            window: ATR period (default: 14)

        Returns:
            DataFrame with ATR column
        """
        df = df.copy()

        # True Range calculation
        tr1 = df['High'] - df['Low']
        tr2 = abs(df['High'] - df['Close'].shift(1))
        tr3 = abs(df['Low'] - df['Close'].shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR (Wilder's method)
        atr = tr.rolling(window=window).mean()

        df['ATR'] = atr
        df['ATR_Percent'] = (atr / df['Close']) * 100  # ATR as % of price

        return df

    @staticmethod
    def calculate_historical_volatility(
        df: pd.DataFrame,
        window: int = 20,
        column: str = 'Close'
    ) -> pd.DataFrame:
        """
        Calculate Historical Volatility (Standard Deviation of returns).

        Args:
            df: OHLCV DataFrame
            window: Lookback period
            column: Column to calculate on

        Returns:
            DataFrame with Historical_Volatility column
        """
        df = df.copy()

        # Calculate returns
        returns = df[column].pct_change()

        # Calculate rolling volatility
        df['Historical_Volatility'] = returns.rolling(window=window).std()

        return df

    @staticmethod
    def calculate_keltner_channel(
        df: pd.DataFrame,
        window: int = 20,
        atr_multiplier: float = 2.0
    ) -> pd.DataFrame:
        """
        Calculate Keltner Channel (EMA ± ATR).

        Args:
            df: OHLCV DataFrame
            window: EMA period
            atr_multiplier: ATR multiplier for channel width

        Returns:
            DataFrame with Keltner channels
        """
        df = df.copy()

        # Middle line (EMA of Close)
        middle = df['Close'].ewm(span=window, adjust=False).mean()

        # ATR
        df = VolatilityIndicators.calculate_atr(df, window=window)
        atr = df['ATR']

        # Channels
        df['KC_Upper'] = middle + (atr * atr_multiplier)
        df['KC_Middle'] = middle
        df['KC_Lower'] = middle - (atr * atr_multiplier)

        return df

    @staticmethod
    def calculate_donchian_channel(
        df: pd.DataFrame,
        window: int = 20
    ) -> pd.DataFrame:
        """
        Calculate Donchian Channel (highest high / lowest low).

        Args:
            df: OHLCV DataFrame
            window: Lookback period

        Returns:
            DataFrame with Donchian channels
        """
        df = df.copy()

        df['DC_High'] = df['High'].rolling(window=window).max()
        df['DC_Low'] = df['Low'].rolling(window=window).min()
        df['DC_Mid'] = (df['DC_High'] + df['DC_Low']) / 2

        return df

    @staticmethod
    def get_bollinger_signal(df: pd.DataFrame) -> Optional[str]:
        """
        Get Bollinger Bands signal (squeeze, expansion, etc).

        Args:
            df: DataFrame with Bollinger Bands calculated

        Returns:
            Signal string or None
        """
        if 'BB_Width' not in df.columns or len(df) < 2:
            return None

        current_width = df['BB_Width'].iloc[-1]
        prev_width = df['BB_Width'].iloc[-2]

        if pd.isna(current_width) or pd.isna(prev_width):
            return None

        # Bollinger Squeeze: bands are getting closer
        if current_width < prev_width * 0.9:  # 10% contraction
            return 'squeeze'
        # Bollinger Expansion: bands are getting wider
        elif current_width > prev_width * 1.1:  # 10% expansion
            return 'expansion'
        else:
            return 'stable'

    @staticmethod
    def get_price_volatility_level(volatility: float, threshold_high: float = 0.03) -> Optional[str]:
        """
        Classify volatility level.

        Args:
            volatility: Historical volatility value (as decimal)
            threshold_high: High volatility threshold

        Returns:
            'low', 'medium', or 'high'
        """
        if pd.isna(volatility):
            return None

        if volatility < threshold_high * 0.5:
            return 'low'
        elif volatility < threshold_high:
            return 'medium'
        else:
            return 'high'


# Convenience functions
def bollinger_bands(
    df: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Quick Bollinger Bands calculation returns (Upper, Middle, Lower)."""
    middle = df['Close'].rolling(window=window).mean()
    std = df['Close'].rolling(window=window).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    return upper, middle, lower


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Quick ATR calculation."""
    tr1 = df['High'] - df['Low']
    tr2 = abs(df['High'] - df['Close'].shift(1))
    tr3 = abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()
