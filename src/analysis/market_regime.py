"""Market regime detection based on SPY, QQQ, and VIX."""

import logging
from typing import Dict, Optional
import pandas as pd
import numpy as np

from config.settings import MARKET_REGIME_MA_PERIOD, VIX_CAUTION_LEVEL, VIX_RISK_OFF_LEVEL

logger = logging.getLogger(__name__)


def calculate_market_regime(
    spy_df: Optional[pd.DataFrame],
    qqq_df: Optional[pd.DataFrame],
    vix_df: Optional[pd.DataFrame],
    ma_period: int = MARKET_REGIME_MA_PERIOD,
    vix_caution: float = VIX_CAUTION_LEVEL,
    vix_risk_off: float = VIX_RISK_OFF_LEVEL
) -> Dict:
    """
    Determine market regime (Safe/Caution/Risk-Off) based on:
    1. SPY and QQQ price vs 20-day moving average
    2. VIX level (volatility index)

    Algorithm:
    - Risk-Off: VIX >= 30 OR (SPY below MA20 AND QQQ below MA20)
    - Caution: VIX >= 20 OR (either SPY or QQQ below MA20)
    - Safe: All conditions good

    Args:
        spy_df: SPY (S&P 500) DataFrame with 'Close' column
        qqq_df: QQQ (NASDAQ 100) DataFrame with 'Close' column (optional)
        vix_df: VIX DataFrame with 'Close' column (optional)
        ma_period: Moving average period (default 20)
        vix_caution: VIX threshold for caution level (default 20)
        vix_risk_off: VIX threshold for risk-off level (default 30)

    Returns:
        Dict with:
            - regime: 'safe' | 'caution' | 'risk_off' | 'unknown'
            - description: Human-readable explanation
            - spy_signal: bool (True if SPY above MA)
            - qqq_signal: bool or None
            - vix_level: float or None
            - details: Dict with component signals
    """
    try:
        if spy_df is None or len(spy_df) < ma_period:
            logger.warning("Insufficient benchmark data for market regime calculation")
            return {
                'regime': 'unknown',
                'description': 'Insufficient data',
                'spy_signal': None,
                'qqq_signal': None,
                'vix_level': None,
                'details': {}
            }

        # Calculate SPY signal
        spy_prices = spy_df['Close'].tail(ma_period + 1)
        spy_current = spy_prices.iloc[-1]
        spy_ma = spy_prices.mean()
        spy_above_ma = spy_current > spy_ma

        # Calculate QQQ signal (if available)
        qqq_above_ma = None
        if qqq_df is not None and len(qqq_df) >= ma_period:
            qqq_prices = qqq_df['Close'].tail(ma_period + 1)
            qqq_current = qqq_prices.iloc[-1]
            qqq_ma = qqq_prices.mean()
            qqq_above_ma = qqq_current > qqq_ma

        # Get VIX level (if available)
        vix_level = None
        if vix_df is not None and len(vix_df) > 0:
            vix_level = float(vix_df['Close'].iloc[-1])

        # Determine regime
        regime = 'safe'
        description = 'Market conditions favorable'

        # Check risk-off conditions
        if vix_level is not None and vix_level >= vix_risk_off:
            regime = 'risk_off'
            description = f'High volatility (VIX: {vix_level:.1f})'
        elif (not spy_above_ma) and (qqq_above_ma is None or not qqq_above_ma):
            regime = 'risk_off'
            description = 'Both SPY and QQQ below 20-day moving average'
        # Check caution conditions
        elif vix_level is not None and vix_level >= vix_caution:
            regime = 'caution'
            description = f'Moderate volatility (VIX: {vix_level:.1f})'
        elif (not spy_above_ma) or (qqq_above_ma is not None and not qqq_above_ma):
            regime = 'caution'
            description = 'One or more indices below 20-day moving average'

        result = {
            'regime': regime,
            'description': description,
            'spy_signal': spy_above_ma,
            'qqq_signal': qqq_above_ma,
            'vix_level': vix_level,
            'details': {
                'spy_price': round(float(spy_current), 2),
                'spy_ma20': round(float(spy_ma), 2),
                'qqq_price': round(float(qqq_prices.iloc[-1]), 2) if qqq_above_ma is not None else None,
                'qqq_ma20': round(float(qqq_prices.mean()), 2) if qqq_above_ma is not None else None,
                'vix_caution_threshold': vix_caution,
                'vix_risk_off_threshold': vix_risk_off
            }
        }

        logger.info(f"Market regime [{regime.upper()}]: {description}")
        return result

    except Exception as e:
        logger.error(f"Error calculating market regime: {e}")
        return {
            'regime': 'unknown',
            'description': f'Error: {str(e)}',
            'spy_signal': None,
            'qqq_signal': None,
            'vix_level': None,
            'details': {}
        }
