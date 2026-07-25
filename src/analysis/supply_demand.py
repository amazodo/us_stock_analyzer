"""Supply & demand analysis including volume profiles and flow estimation."""

import logging
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SupplyDemandAnalysis:
    """Analyze supply/demand dynamics from price and volume."""

    @staticmethod
    def calculate_vwap_position(df: pd.DataFrame) -> Optional[float]:
        """
        Calculate current price position relative to VWAP (0-1 scale).
        > 0.5 = price above VWAP (bullish)
        < 0.5 = price below VWAP (bearish)

        Args:
            df: OHLCV DataFrame

        Returns:
            Position score (0-1) or None
        """
        if len(df) < 20:
            return None

        try:
            # Calculate VWAP
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            vwap = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

            current_price = df['Close'].iloc[-1]
            current_vwap = vwap.iloc[-1]

            # Find min/max over lookback
            lookback = min(20, len(vwap))
            vwap_min = vwap.iloc[-lookback:].min()
            vwap_max = vwap.iloc[-lookback:].max()

            if vwap_max == vwap_min:
                return 0.5

            # Normalize position
            position = (current_price - vwap_min) / (vwap_max - vwap_min)
            return min(1.0, max(0.0, position))

        except Exception as e:
            logger.error(f"Error calculating VWAP position: {e}")
            return None

    @staticmethod
    def detect_volume_spike(df: pd.DataFrame, threshold: float = 1.5, window: int = 20) -> bool:
        """
        Detect abnormal volume increase (institutional inflow indicator).

        Args:
            df: OHLCV DataFrame
            threshold: Multiplier of average volume (1.5 = 50% above average)
            window: Lookback window for average

        Returns:
            True if volume spike detected, False otherwise
        """
        if len(df) < window:
            return False

        try:
            avg_volume = df['Volume'].iloc[-window:-1].mean()
            current_volume = df['Volume'].iloc[-1]

            return current_volume > (avg_volume * threshold)

        except Exception as e:
            logger.error(f"Error detecting volume spike: {e}")
            return False

    @staticmethod
    def calculate_volume_profile(
        df: pd.DataFrame,
        num_bins: int = 10
    ) -> Dict:
        """
        Calculate volume profile (price levels with highest trading volume).
        Identifies key support/resistance zones.

        Args:
            df: OHLCV DataFrame
            num_bins: Number of price bins

        Returns:
            Dictionary with volume profile data
        """
        if len(df) < 20:
            return {}

        try:
            # Create price bins
            price_min = df['Low'].min()
            price_max = df['High'].max()

            bins = np.linspace(price_min, price_max, num_bins + 1)
            bin_centers = (bins[:-1] + bins[1:]) / 2

            # Aggregate volume in each bin
            bin_volumes = np.zeros(num_bins)

            for idx, row in df.iterrows():
                for i in range(num_bins):
                    if bins[i] <= row['Close'] <= bins[i + 1]:
                        bin_volumes[i] += row['Volume']
                        break

            # Find peak volume levels
            peak_indices = np.argsort(bin_volumes)[-3:]  # Top 3

            profile = {
                'bin_centers': bin_centers.tolist(),
                'bin_volumes': bin_volumes.tolist(),
                'peak_levels': [float(bin_centers[i]) for i in peak_indices if bin_volumes[i] > 0],
                'current_price': float(df['Close'].iloc[-1]),
            }

            return profile

        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return {}

    @staticmethod
    def estimate_institutional_demand(
        df: pd.DataFrame,
        window: int = 20
    ) -> float:
        """
        Estimate institutional demand based on volume-weighted price moves.
        Score from -1 (institutional selling) to +1 (institutional buying).

        Args:
            df: OHLCV DataFrame
            window: Lookback period

        Returns:
            Institutional flow score (-1 to +1)
        """
        if len(df) < window:
            return 0.0

        try:
            # Calculate daily returns
            returns = df['Close'].pct_change()

            # Weight by volume
            avg_volume = df['Volume'].mean()
            volume_ratio = df['Volume'] / avg_volume

            # Recent period
            recent_returns = returns.iloc[-window:].values
            recent_volumes = volume_ratio.iloc[-window:].values

            # Institutional flow: large volume on up days = buying, large volume on down days = selling
            flow_scores = recent_returns * recent_volumes

            institutional_score = flow_scores.mean()

            # Normalize to -1 to +1
            if abs(institutional_score) > 0:
                institutional_score = np.tanh(institutional_score)

            return float(institutional_score)

        except Exception as e:
            logger.error(f"Error estimating institutional demand: {e}")
            return 0.0

    @staticmethod
    def calculate_atr_volatility_filter(
        df: pd.DataFrame,
        target_gain: float = 5.0,
        period: int = 14
    ) -> Tuple[float, bool]:
        """
        Calculate if stock has sufficient volatility to achieve 5% weekly gain.
        Uses ATR (Average True Range) as measure.

        Args:
            df: OHLCV DataFrame
            target_gain: Target gain percentage (default: 5%)
            period: ATR period

        Returns:
            Tuple of (atr_percentage, is_feasible)
            - atr_percentage: ATR as % of current price
            - is_feasible: True if 5% gain is physically possible with current volatility
        """
        if len(df) < period:
            return 0.0, False

        try:
            # Calculate ATR
            tr1 = df['High'] - df['Low']
            tr2 = abs(df['High'] - df['Close'].shift(1))
            tr3 = abs(df['Low'] - df['Close'].shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()

            current_atr = atr.iloc[-1]
            current_price = df['Close'].iloc[-1]

            if pd.isna(current_atr) or current_price <= 0:
                return 0.0, False

            # ATR as percentage of price
            atr_pct = (current_atr / current_price) * 100

            # 5% gain is feasible if ATR >= ~2.5% (conservative estimate)
            # Rationale: 1 ATR move = 1 week volatility, so ATR > 2.5% allows 5% target
            is_feasible = atr_pct >= (target_gain / 2.0)

            return round(atr_pct, 2), is_feasible

        except Exception as e:
            logger.error(f"Error calculating ATR filter: {e}")
            return 0.0, False


def analyze_supply_demand(df: pd.DataFrame) -> Dict:
    """
    Complete supply/demand analysis for a stock.

    Args:
        df: OHLCV DataFrame

    Returns:
        Dictionary with complete supply/demand metrics
    """
    analyzer = SupplyDemandAnalysis()

    vwap_position = analyzer.calculate_vwap_position(df)
    volume_spike = analyzer.detect_volume_spike(df)
    profile = analyzer.calculate_volume_profile(df)
    institutional_flow = analyzer.estimate_institutional_demand(df)
    atr_pct, atr_feasible = analyzer.calculate_atr_volatility_filter(df)

    return {
        'vwap_position': round(vwap_position, 3) if vwap_position else None,
        'vwap_signal': 'bullish' if vwap_position and vwap_position > 0.5 else 'bearish' if vwap_position else None,
        'volume_spike': volume_spike,
        'volume_profile': profile,
        'institutional_flow_score': round(institutional_flow, 3),
        'institutional_signal': 'buying' if institutional_flow > 0.2 else 'selling' if institutional_flow < -0.2 else 'neutral',
        'atr_pct': atr_pct,
        'atr_5pct_feasible': atr_feasible,
    }
