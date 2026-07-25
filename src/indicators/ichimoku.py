"""Ichimoku Cloud indicator calculation."""

import logging
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class IchimokuIndicators:
    """Calculate Ichimoku Cloud technical indicator."""

    @staticmethod
    def calculate_ichimoku(
        df: pd.DataFrame,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
        displacement: int = 26
    ) -> pd.DataFrame:
        """
        Calculate Ichimoku Cloud (Ichimoku Kinko Hyo).

        Args:
            df: OHLCV DataFrame with columns: Open, High, Low, Close, Volume
            tenkan_period: Period for Tenkan-sen (default 9)
            kijun_period: Period for Kijun-sen (default 26)
            senkou_b_period: Period for Senkou Span B (default 52)
            displacement: Displacement (shift) for forward shift (default 26)

        Returns:
            DataFrame with added Ichimoku columns:
            - Ichimoku_Tenkan: Tenkan-sen (Conversion Line)
            - Ichimoku_Kijun: Kijun-sen (Base Line)
            - Ichimoku_SenkouA: Senkou Span A (Leading Span A)
            - Ichimoku_SenkouB: Senkou Span B (Leading Span B)
            - Ichimoku_Chikou: Chikou Span (Lagging Span)
        """
        try:
            df = df.copy()

            # Calculate Tenkan-sen (9-period high/low midpoint)
            high_9 = df['High'].rolling(window=tenkan_period).max()
            low_9 = df['Low'].rolling(window=tenkan_period).min()
            df['Ichimoku_Tenkan'] = (high_9 + low_9) / 2

            # Calculate Kijun-sen (26-period high/low midpoint)
            high_26 = df['High'].rolling(window=kijun_period).max()
            low_26 = df['Low'].rolling(window=kijun_period).min()
            df['Ichimoku_Kijun'] = (high_26 + low_26) / 2

            # Calculate Senkou Span A (average of Tenkan + Kijun, shifted forward 26 days)
            senkou_a = (df['Ichimoku_Tenkan'] + df['Ichimoku_Kijun']) / 2
            df['Ichimoku_SenkouA'] = senkou_a.shift(displacement)

            # Calculate Senkou Span B (52-period high/low midpoint, shifted forward 26 days)
            high_52 = df['High'].rolling(window=senkou_b_period).max()
            low_52 = df['Low'].rolling(window=senkou_b_period).min()
            senkou_b = (high_52 + low_52) / 2
            df['Ichimoku_SenkouB'] = senkou_b.shift(displacement)

            # Calculate Chikou Span (current close, shifted back 26 days)
            df['Ichimoku_Chikou'] = df['Close'].shift(-displacement)

            logger.debug(f"OK Calculated Ichimoku indicators for {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"Error calculating Ichimoku: {e}")
            return df

    @staticmethod
    def get_ichimoku_signal(df: pd.DataFrame) -> Optional[str]:
        """
        Generate Ichimoku trading signal based on current state.

        Args:
            df: DataFrame with calculated Ichimoku indicators

        Returns:
            'bullish', 'bearish', 'neutral', or None if insufficient data
        """
        try:
            if len(df) < 2:
                return None

            required_cols = ['Ichimoku_Tenkan', 'Ichimoku_Kijun', 'Close',
                           'Ichimoku_SenkouA', 'Ichimoku_SenkouB']
            if not all(col in df.columns for col in required_cols):
                return None

            current = df.iloc[-1]
            prev = df.iloc[-2]

            # Current values
            tenkan = current['Ichimoku_Tenkan']
            kijun = current['Ichimoku_Kijun']
            close = current['Close']
            senkou_a = current['Ichimoku_SenkouA']
            senkou_b = current['Ichimoku_SenkouB']

            # Previous values for crossover detection
            prev_tenkan = prev['Ichimoku_Tenkan']
            prev_kijun = prev['Ichimoku_Kijun']

            # Signals
            signal_count = 0

            # 1. Price above cloud (bullish)
            if pd.notna(senkou_a) and pd.notna(senkou_b):
                kumo_top = max(senkou_a, senkou_b)
                if close > kumo_top:
                    signal_count += 2
                elif close < min(senkou_a, senkou_b):
                    signal_count -= 2

            # 2. Tenkan > Kijun (bullish cross)
            if pd.notna(tenkan) and pd.notna(kijun):
                if tenkan > kijun:
                    signal_count += 1
                else:
                    signal_count -= 1

                # Bullish crossover (Tenkan crosses above Kijun)
                if prev_tenkan <= prev_kijun and tenkan > kijun:
                    signal_count += 1

            # Determine overall signal
            if signal_count >= 2:
                return 'bullish'
            elif signal_count <= -2:
                return 'bearish'
            else:
                return 'neutral'

        except Exception as e:
            logger.warning(f"Error generating Ichimoku signal: {e}")
            return None
