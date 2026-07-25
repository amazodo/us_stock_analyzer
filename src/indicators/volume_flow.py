"""Volume and order flow indicators: OBV, VPTC, Volume Profile."""

import logging
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class VolumeFlowIndicators:
    """Calculate volume and order flow technical indicators."""

    @staticmethod
    def calculate_obv(
        df: pd.DataFrame,
        column: str = 'Close'
    ) -> pd.DataFrame:
        """
        Calculate On-Balance Volume (OBV).

        Args:
            df: OHLCV DataFrame
            column: Price column to compare

        Returns:
            DataFrame with OBV column
        """
        df = df.copy()

        # Determine if close is up or down
        price_change = df[column].diff()
        volume_with_sign = np.where(price_change > 0, df['Volume'],
                                     np.where(price_change < 0, -df['Volume'], 0))

        df['OBV'] = volume_with_sign.cumsum()

        return df

    @staticmethod
    def calculate_obv_ma(
        df: pd.DataFrame,
        obv_window: int = 20,
        column: str = 'Close'
    ) -> pd.DataFrame:
        """
        Calculate OBV with moving average.

        Args:
            df: OHLCV DataFrame
            obv_window: OBV MA period
            column: Price column

        Returns:
            DataFrame with OBV and OBV_MA
        """
        df = VolumeFlowIndicators.calculate_obv(df, column=column)
        df[f'OBV_MA_{obv_window}'] = df['OBV'].rolling(window=obv_window).mean()

        return df

    @staticmethod
    def calculate_volume_sma(
        df: pd.DataFrame,
        window: int = 20
    ) -> pd.DataFrame:
        """
        Calculate Simple Moving Average of Volume.

        Args:
            df: OHLCV DataFrame
            window: MA period for volume

        Returns:
            DataFrame with Volume_SMA column
        """
        df = df.copy()
        df[f'Volume_SMA_{window}'] = df['Volume'].rolling(window=window).mean()

        return df

    @staticmethod
    def calculate_volume_trend(
        df: pd.DataFrame,
        window: int = 10
    ) -> pd.DataFrame:
        """
        Calculate volume trend ratio (current volume / average volume).

        Args:
            df: OHLCV DataFrame
            window: Lookback period for average

        Returns:
            DataFrame with Volume_Trend column
        """
        df = df.copy()

        volume_avg = df['Volume'].rolling(window=window).mean()
        df['Volume_Trend'] = df['Volume'] / volume_avg

        return df

    @staticmethod
    def calculate_accumulation_distribution(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Accumulation/Distribution Line.

        Args:
            df: OHLCV DataFrame (must have High, Low, Close, Volume)

        Returns:
            DataFrame with AD_Line column
        """
        df = df.copy()

        # CLV (Close Location Value)
        clv = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / \
              (df['High'] - df['Low'])
        clv = clv.fillna(0)  # Handle division by zero

        # A/D Line
        df['AD_Line'] = (clv * df['Volume']).cumsum()

        return df

    @staticmethod
    def calculate_money_flow_index(
        df: pd.DataFrame,
        window: int = 14
    ) -> pd.DataFrame:
        """
        Calculate Money Flow Index (MFI).

        Args:
            df: OHLCV DataFrame
            window: MFI period

        Returns:
            DataFrame with MFI column
        """
        df = df.copy()

        # Typical Price
        tp = (df['High'] + df['Low'] + df['Close']) / 3

        # Raw Money Flow
        rmf = tp * df['Volume']

        # Positive/Negative Money Flow
        price_change = tp.diff()
        pmf = rmf.where(price_change > 0, 0)
        nmf = rmf.where(price_change < 0, 0)

        # Money Flow Ratio
        pmf_sum = pmf.rolling(window=window).sum()
        nmf_sum = nmf.rolling(window=window).sum()

        mfr = pmf_sum / nmf_sum.replace(0, 1e-10)

        # MFI
        df['MFI'] = 100 - (100 / (1 + mfr))

        return df

    @staticmethod
    def get_volume_signal(df: pd.DataFrame, window: int = 20) -> Optional[str]:
        """
        Get volume signal (increasing, decreasing, average).

        Args:
            df: DataFrame with volume data
            window: Lookback period

        Returns:
            Signal string or None
        """
        if len(df) < window + 1:
            return None

        current_volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].iloc[-window:-1].mean()

        if pd.isna(current_volume) or pd.isna(avg_volume):
            return None

        if current_volume > avg_volume * 1.2:  # 20% above average
            return 'increasing'
        elif current_volume < avg_volume * 0.8:  # 20% below average
            return 'decreasing'
        else:
            return 'average'

    @staticmethod
    def get_obv_signal(df: pd.DataFrame, obv_window: int = 20) -> Optional[str]:
        """
        Get OBV signal based on OBV vs its MA.

        Args:
            df: DataFrame with OBV calculated
            obv_window: OBV MA period

        Returns:
            'bullish', 'bearish', or 'neutral'
        """
        if 'OBV' not in df.columns or len(df) < obv_window + 1:
            return None

        df = VolumeFlowIndicators.calculate_obv_ma(df, obv_window=obv_window)

        current_obv = df['OBV'].iloc[-1]
        obv_ma = df[f'OBV_MA_{obv_window}'].iloc[-1]

        if pd.isna(current_obv) or pd.isna(obv_ma):
            return None

        if current_obv > obv_ma:
            return 'bullish'
        elif current_obv < obv_ma:
            return 'bearish'
        else:
            return 'neutral'

    @staticmethod
    def estimate_institutional_flow(
        df: pd.DataFrame,
        window: int = 20
    ) -> Optional[float]:
        """
        Estimate institutional flow based on volume spikes and price movement.
        Returns a score from -1 (selling) to +1 (buying).

        Args:
            df: OHLCV DataFrame
            window: Lookback period

        Returns:
            Flow score (-1 to +1) or None
        """
        if len(df) < window + 1:
            return None

        df = df.copy()

        # Calculate returns and volume trend
        returns = df['Close'].pct_change()
        volume_avg = df['Volume'].rolling(window=window).mean()
        volume_ratio = df['Volume'] / volume_avg

        # Institutional flow metric
        recent_returns = returns.iloc[-window:]
        recent_volumes = volume_ratio.iloc[-window:]

        # Positive flow: large volume on up days
        # Negative flow: large volume on down days
        flow = ((recent_returns * recent_volumes).sum() / len(recent_returns))

        # Normalize to -1 to +1
        return min(1, max(-1, flow / 0.05))  # Empirical normalization


# Convenience functions
def obv(df: pd.DataFrame) -> pd.Series:
    """Quick OBV calculation."""
    price_change = df['Close'].diff()
    return (np.where(price_change > 0, df['Volume'],
                     np.where(price_change < 0, -df['Volume'], 0))).cumsum()


def mfi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Quick MFI calculation."""
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    rmf = tp * df['Volume']
    price_change = tp.diff()
    pmf = rmf.where(price_change > 0, 0)
    nmf = rmf.where(price_change < 0, 0)
    mfr = pmf.rolling(window=window).sum() / nmf.rolling(window=window).sum().replace(0, 1e-10)
    return 100 - (100 / (1 + mfr))
