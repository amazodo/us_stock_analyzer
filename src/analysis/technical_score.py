"""Technical score calculation from indicators."""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from config.settings import TECHNICAL_WEIGHTS, ATR_FEASIBILITY_THRESHOLD_PCT
from src.indicators.moving_averages import MovingAverageIndicators
from src.indicators.momentum import MomentumIndicators
from src.indicators.volatility import VolatilityIndicators
from src.indicators.volume_flow import VolumeFlowIndicators
from src.analysis.supply_demand import analyze_supply_demand

logger = logging.getLogger(__name__)


class TechnicalScoreCalculator:
    """Calculate technical score from multiple indicators."""

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or TECHNICAL_WEIGHTS

    def calculate_moving_average_score(self, df: pd.DataFrame) -> float:
        """
        Score based on moving average trends.
        0-100 scale, higher = more bullish.

        Improved logic:
        - Hierarchical price position (most significant level only)
        - Weighted MA alignment signal
        - EMA momentum confirmation

        Args:
            df: OHLCV DataFrame with MA indicators

        Returns:
            Score (0-100)
        """
        if len(df) < 200:
            return 50.0  # Neutral if insufficient data

        try:
            # Calculate if not already present
            if 'SMA_20' not in df.columns:
                df = MovingAverageIndicators.calculate_multiple_smas(df, periods=[20, 50, 200])
            if 'EMA_12' not in df.columns:
                df = MovingAverageIndicators.calculate_multiple_emas(df, periods=[12, 26])

            latest_price = df['Close'].iloc[-1]
            sma_20 = df['SMA_20'].iloc[-1]
            sma_50 = df['SMA_50'].iloc[-1]
            sma_200 = df['SMA_200'].iloc[-1]
            ema_12 = df['EMA_12'].iloc[-1]
            ema_26 = df['EMA_26'].iloc[-1]

            score = 50.0  # Base score

            # Improved: Hierarchical price position (avoid redundant double-counting)
            # Only the strongest level is counted to reduce bias
            if pd.notna(sma_200) and latest_price > sma_200:
                score += 15  # Long-term bullish trend (strongest signal)
            elif pd.notna(sma_50) and latest_price > sma_50:
                score += 10  # Mid-term bullish trend
            elif pd.notna(sma_20) and latest_price > sma_20:
                score += 5   # Short-term bullish trend

            # Moving average alignment (bullish) - Golden Cross
            # Adjusted weight for better balance
            if pd.notna(sma_200) and pd.notna(sma_50) and pd.notna(sma_20):
                if sma_20 > sma_50 > sma_200:
                    score += 15  # Strong uptrend alignment

            # EMA alignment - Fast momentum confirmation
            if pd.notna(ema_12) and pd.notna(ema_26):
                if ema_12 > ema_26:
                    score += 10  # Short-term momentum bullish

            return min(100, max(0, score))

        except Exception as e:
            logger.error(f"Error calculating MA score: {e}")
            return 50.0

    def calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """
        Score based on RSI, MACD, Stochastic momentum.
        Improved logic:
        - Symmetric RSI overbought/oversold scoring
        - MACD zero-line crossing
        - Stochastic oscillator signals

        Args:
            df: OHLCV DataFrame with momentum indicators

        Returns:
            Score (0-100)
        """
        try:
            if 'RSI_14' not in df.columns:
                df = MomentumIndicators.calculate_rsi(df, window=14)
            if 'MACD' not in df.columns:
                df = MomentumIndicators.calculate_macd(df)
            if 'Stochastic_%K' not in df.columns:
                df = MomentumIndicators.calculate_stochastic(df)

            rsi = df['RSI_14'].iloc[-1]
            macd = df['MACD'].iloc[-1]
            macd_signal = df['MACD_Signal'].iloc[-1]
            stoch_k = df['Stochastic_%K'].iloc[-1]
            stoch_d = df['Stochastic_%D'].iloc[-1]

            score = 50.0  # Base score

            # RSI scoring - Improved: Symmetric strength
            if pd.notna(rsi):
                if 30 < rsi < 70:
                    score += 10  # Neutral zone
                elif rsi < 30:
                    score += 20  # Oversold (bullish reversal)
                elif rsi > 70:
                    score -= 15  # Overbought (bearish) - Improved: -10 → -15

            # MACD line vs signal line
            if pd.notna(macd) and pd.notna(macd_signal):
                if macd > macd_signal:
                    score += 15  # MACD above signal (momentum up)
                elif macd < macd_signal:
                    score -= 15  # MACD below signal (momentum down)

            # MACD zero-line crossing - Improved: Added negative case
            if pd.notna(macd):
                if macd > 0:
                    score += 10  # Above zero line (uptrend)
                elif macd < 0:
                    score -= 5   # Below zero line (downtrend) - Improved: Added

            # Stochastic oscillator - NEW
            if pd.notna(stoch_k):
                if stoch_k < 20:
                    score += 10  # Oversold (bullish)
                elif stoch_k > 80:
                    score -= 10  # Overbought (bearish)

                # Stochastic crossover (optional)
                if pd.notna(stoch_d):
                    if stoch_k > stoch_d:
                        score += 5   # %K above %D (momentum gain)
                    elif stoch_k < stoch_d:
                        score -= 5   # %K below %D (momentum loss)

            return min(100, max(0, score))

        except Exception as e:
            logger.error(f"Error calculating momentum score: {e}")
            return 50.0

    def calculate_volatility_score(self, df: pd.DataFrame, beta: float = None) -> float:
        """
        Score based on Bollinger Bands, ATR, and Beta.
        Improved logic:
        - Symmetric Bollinger Bands scoring (+20/-20)
        - Enhanced ATR interpolation (5-level)
        - Beta sensitivity adjustment (offensive/defensive)
        - Hierarchical structure (avoid double-counting)

        Args:
            df: OHLCV DataFrame with volatility indicators
            beta: Beta coefficient (optional, for market sensitivity)

        Returns:
            Score (0-100)
        """
        try:
            if 'BB_Upper' not in df.columns:
                df = VolatilityIndicators.calculate_bollinger_bands(df, window=20)
            if 'ATR' not in df.columns:
                df = VolatilityIndicators.calculate_atr(df, window=14)

            price = df['Close'].iloc[-1]
            bb_position = df['BB_Position'].iloc[-1]
            atr_pct = (df['ATR'].iloc[-1] / price) * 100

            score = 50.0  # Base score

            # Improved: Hierarchical Bollinger Bands position
            # Only strongest level counted (avoid double-counting)
            if pd.notna(bb_position):
                if bb_position > 0.8:
                    score += 20  # Strong bullish (price near upper band)
                elif bb_position > 0.6:
                    score += 10  # Mild bullish
                elif bb_position > 0.4:
                    score += 0   # Neutral-bullish
                elif bb_position > 0.2:
                    score -= 5   # Neutral-bearish
                elif bb_position < 0.2:
                    score -= 20  # Improved: -10 → -20 (symmetric with +20)

            # Improved: Enhanced ATR interpolation (5-level)
            if pd.notna(atr_pct):
                if atr_pct < 1:
                    score -= 5   # Extremely low volatility (5% unattainable)
                elif atr_pct < 2:
                    score += 5   # Low volatility
                elif atr_pct < 3:
                    score += 10  # Moderate volatility (optimal)
                elif atr_pct < 5:
                    score += 0   # Medium-high volatility (neutral)
                else:
                    score -= 10  # Very high volatility (risky)

            # Improved: Beta sensitivity adjustment (NEW)
            if beta is not None and pd.notna(beta):
                if beta > 1.2:
                    score += 10  # Aggressive (high beta, beats market in uptrend)
                elif beta > 1.0:
                    score += 5   # Slightly aggressive
                elif beta < 0.8:
                    score -= 5   # Defensive (low beta, beats market in downtrend)
                elif beta < 0.6:
                    score -= 10  # Very defensive

            return min(100, max(0, score))

        except Exception as e:
            logger.error(f"Error calculating volatility score: {e}")
            return 50.0

    def calculate_volume_score(self, df: pd.DataFrame) -> float:
        """
        Score based on volume and OBV trends.
        Improved logic:
        - OBV strength measurement (not just direction)
        - Volume trend with decrease penalty
        - MFI (Money Flow Index) for flow strength

        Args:
            df: OHLCV DataFrame with volume indicators

        Returns:
            Score (0-100)
        """
        try:
            if 'Volume_SMA_20' not in df.columns:
                df = VolumeFlowIndicators.calculate_volume_sma(df, window=20)
            if 'OBV' not in df.columns:
                df = VolumeFlowIndicators.calculate_obv(df)
            if 'MFI' not in df.columns:
                df = VolumeFlowIndicators.calculate_money_flow_index(df, window=14)

            volume = df['Volume'].iloc[-1]
            volume_avg = df['Volume_SMA_20'].iloc[-1]
            volume_trend = volume / volume_avg

            score = 50.0  # Base score

            # Improved: Volume trend with granularity
            if pd.notna(volume_trend):
                if volume_trend > 1.2:
                    score += 15  # 20%+ above average
                elif volume_trend > 1.0:
                    score += 10  # 0-20% above
                elif volume_trend < 0.8:
                    score -= 5   # NEW: 20% below average (weakness)

            # Improved: OBV trend with strength measurement
            if len(df) > 20 and pd.notna(df['OBV'].iloc[-1]):
                obv_recent = df['OBV'].iloc[-5:].mean()
                obv_older = df['OBV'].iloc[-25:-5].mean()

                if pd.notna(obv_recent) and pd.notna(obv_older):
                    obv_diff = obv_recent - obv_older
                    obv_strength = obv_diff / max(abs(obv_older), 1)

                    if obv_strength > 0.1:
                        score += 15  # NEW: Strong uptrend
                    elif obv_strength > 0.02:
                        score += 10  # Weak uptrend
                    elif obv_strength < -0.1:
                        score -= 15  # NEW: Strong downtrend
                    elif obv_strength < -0.02:
                        score -= 5   # NEW: Weak downtrend

            # Improved: MFI signal (NEW)
            if pd.notna(df['MFI'].iloc[-1]):
                mfi = df['MFI'].iloc[-1]
                if mfi > 80:
                    score += 10  # Overbought (reversal signal)
                elif mfi > 60:
                    score += 5   # Strong money inflow
                elif mfi < 20:
                    score -= 10  # Oversold (reversal signal)
                elif mfi < 40:
                    score -= 5   # Weak money flow

            return min(100, max(0, score))

        except Exception as e:
            logger.error(f"Error calculating volume score: {e}")
            return 50.0

    def calculate_fibonacci_score(self, df: pd.DataFrame) -> float:
        """
        Score based on Fibonacci retracement levels.
        Improved logic:
        - 50% level added (requirement compliance)
        - Symmetric scoring (+20/-20)
        - Trend-aware signals
        - Reversal signals at extremes

        Args:
            df: OHLCV DataFrame

        Returns:
            Score (0-100)
        """
        try:
            from src.analysis.fibonacci import analyze_fibonacci

            fib_analysis = analyze_fibonacci(df)
            if not fib_analysis:
                return 50.0

            current_price = fib_analysis.get('current_price', 0)
            levels = fib_analysis.get('retracement_levels', {})
            trend = fib_analysis.get('trend', 'neutral')
            swing_low = fib_analysis.get('swing_low', 0)
            swing_high = fib_analysis.get('swing_high', 0)

            if not levels or current_price <= 0:
                return 50.0

            score = 50.0  # Base score

            # Get Fibonacci levels (Improved: 50% added)
            level_618 = levels.get('61.8%', current_price)
            level_500 = levels.get('50%', current_price)    # NEW: 50% level
            level_382 = levels.get('38.2%', current_price)
            level_236 = levels.get('23.6%', current_price)

            # Improved: Hierarchical price position (strongest signal only)
            if pd.notna(current_price) and pd.notna(level_618):
                if current_price > level_618:
                    score += 20  # Strong bullish (broke key resistance)
                elif current_price > level_500:
                    score += 10  # Improved: 50% level added (was missing)
                elif current_price > level_382:
                    score += 5   # Mild bullish (at support)
                elif current_price > level_236:
                    score -= 5   # Mild bearish
                elif current_price > swing_low:
                    score -= 10  # Weak (between swing low and 23.6%)
                else:
                    score -= 20  # Improved: -10 → -20 (symmetric with +20)

            # Improved: Reversal signals at extremes (NEW)
            if trend == 'downtrend' and pd.notna(current_price) and pd.notna(level_236):
                # In downtrend, at extreme low = reversal signal
                if current_price <= level_236 and current_price > swing_low:
                    score += 15  # Strong reversal signal (oversold bounce)

            if trend == 'uptrend' and pd.notna(current_price) and pd.notna(level_500):
                # In uptrend, 50% is important psychological level
                if current_price > level_500 and current_price < level_618:
                    score += 5   # Mild reversal/continuation signal

            return min(100, max(0, score))

        except Exception as e:
            logger.error(f"Error calculating Fibonacci score: {e}")
            return 50.0

    def calculate_ichimoku_score(self, df: pd.DataFrame) -> float:
        """
        Score based on Ichimoku Cloud indicator.

        Scoring components:
        - Price position vs cloud (Kumo): above +20 / within 0 / below -20
        - Cloud color (Senkou A vs B): strong (A>B) +10 / weak (A<B) -10
        - Tenkan-sen vs Kijun-sen: crossover/alignment signal +10 / opposite -5
        - Chikou span confirmation: price above past price +10

        Args:
            df: OHLCV DataFrame with Ichimoku indicators

        Returns:
            Score (0-100)
        """
        try:
            # Minimum data requirement: Senkou B period (52) + displacement (26) = 78 days
            if len(df) < 78:
                return 50.0  # Neutral if insufficient data

            from src.indicators.ichimoku import IchimokuIndicators

            # Calculate Ichimoku if not already present
            if 'Ichimoku_Tenkan' not in df.columns:
                df = IchimokuIndicators.calculate_ichimoku(df)

            required_cols = ['Ichimoku_Tenkan', 'Ichimoku_Kijun', 'Close',
                           'Ichimoku_SenkouA', 'Ichimoku_SenkouB', 'Ichimoku_Chikou']
            if not all(col in df.columns for col in required_cols):
                return 50.0

            current = df.iloc[-1]
            score = 50.0  # Base score

            # Get current values
            close = current['Close']
            tenkan = current['Ichimoku_Tenkan']
            kijun = current['Ichimoku_Kijun']
            senkou_a = current['Ichimoku_SenkouA']
            senkou_b = current['Ichimoku_SenkouB']
            chikou = current['Ichimoku_Chikou']

            # 1. Price vs Kumo (cloud) position
            if pd.notna(senkou_a) and pd.notna(senkou_b):
                kumo_top = max(senkou_a, senkou_b)
                kumo_bottom = min(senkou_a, senkou_b)

                if close > kumo_top:
                    score += 20  # Strong bullish: price above cloud
                elif close < kumo_bottom:
                    score -= 20  # Strong bearish: price below cloud
                else:
                    score += 0   # Neutral: price within cloud

            # 2. Cloud color (Senkou A vs B)
            if pd.notna(senkou_a) and pd.notna(senkou_b):
                if senkou_a > senkou_b:
                    score += 10  # Bullish cloud (A above B)
                elif senkou_a < senkou_b:
                    score -= 10  # Bearish cloud (A below B)

            # 3. Tenkan-sen vs Kijun-sen crossover/alignment
            if pd.notna(tenkan) and pd.notna(kijun):
                if tenkan > kijun:
                    score += 10  # Bullish: Tenkan above Kijun (golden cross signal)
                else:
                    score -= 5   # Bearish: Tenkan below Kijun (death cross signal)

            # 4. Chikou span confirmation (price above 26-day-ago close)
            if pd.notna(chikou) and len(df) > 26:
                past_close = df.iloc[-27]['Close']  # 26 days ago
                if close > past_close:
                    score += 10  # Bullish: current price in uptrend vs 26d ago
                else:
                    score -= 5   # Bearish: current price weaker than 26d ago

            return min(100, max(0, score))

        except Exception as e:
            logger.error(f"Error calculating Ichimoku score: {e}")
            return 50.0

    def calculate_supply_demand_score(self, df: pd.DataFrame) -> float:
        """
        Score based on supply/demand analysis (VWAP, volume spike, institutional flow, AD_Line).
        Improved logic:
        - Symmetric VWAP scoring
        - Granular institutional flow thresholds
        - AD_Line accumulation/distribution tracking

        Args:
            df: OHLCV DataFrame

        Returns:
            Score (0-100)
        """
        try:
            sd_analysis = analyze_supply_demand(df)

            score = 50.0  # Base score

            # Improved: VWAP position with better symmetry
            vwap_pos = sd_analysis.get('vwap_position', 0.5)
            if pd.notna(vwap_pos):
                if vwap_pos > 0.8:
                    score += 20  # Strong bullish (price well above VWAP)
                elif vwap_pos > 0.6:
                    score += 15  # Bullish
                elif vwap_pos > 0.4:
                    score += 5   # Mild bullish
                elif vwap_pos > 0.2:
                    score -= 5   # Mild bearish
                elif vwap_pos <= 0.2:
                    score -= 20  # NEW: Strong bearish (symmetric)

            # Volume spike (institutional activity)
            if sd_analysis.get('volume_spike', False):
                score += 10

            # Improved: Institutional flow with granular thresholds
            inst_flow = sd_analysis.get('institutional_flow_score', 0.0)
            if pd.notna(inst_flow):
                if inst_flow > 0.3:
                    score += 15  # Strong institutional buying
                elif inst_flow > 0.15:
                    score += 10  # NEW: Medium buying
                elif inst_flow > 0.05:
                    score += 5   # Weak buying
                elif inst_flow < -0.3:
                    score -= 15  # Strong institutional selling
                elif inst_flow < -0.15:
                    score -= 10  # NEW: Medium selling
                elif inst_flow < -0.05:
                    score -= 5   # NEW: Weak selling

            # Improved: AD_Line trend (NEW)
            if len(df) > 10:
                try:
                    if 'AD_Line' not in df.columns:
                        df = VolumeFlowIndicators.calculate_accumulation_distribution(df)

                    if pd.notna(df['AD_Line'].iloc[-1]):
                        ad_recent = df['AD_Line'].iloc[-5:].mean()
                        ad_older = df['AD_Line'].iloc[-15:-5].mean()

                        if pd.notna(ad_recent) and pd.notna(ad_older):
                            if ad_recent > ad_older:
                                score += 5   # Capital inflow (accumulation)
                            else:
                                score -= 5   # Capital outflow (distribution)
                except Exception:
                    pass  # AD_Line calculation optional

            # NOTE: ATR feasibility nudge removed (now handled by hard filter in pipeline)

            return min(100, max(0, score))

        except Exception as e:
            logger.error(f"Error calculating supply/demand score: {e}")
            return 50.0

    def calculate_volume_flow_score(self, df: pd.DataFrame) -> Tuple[float, Dict]:
        """
        Combined OBV/volume + VWAP/spike/institutional flow score.
        Merges calculate_volume_score and calculate_supply_demand_score into one 20% bucket.

        Args:
            df: OHLCV DataFrame

        Returns:
            Tuple of (combined_score, component_dict)
        """
        try:
            volume_score = self.calculate_volume_score(df)
            sd_score = self.calculate_supply_demand_score(df)

            # Simple average of both components
            combined = round((volume_score + sd_score) / 2, 1)

            component_detail = {
                'volume_score': round(volume_score, 1),
                'supply_demand_score': round(sd_score, 1)
            }

            return combined, component_detail

        except Exception as e:
            logger.error(f"Error calculating volume_flow score: {e}")
            return 50.0, {'volume_score': 50.0, 'supply_demand_score': 50.0}

    def calculate_overall_technical_score(
        self,
        df: pd.DataFrame,
        selected_components: Optional[List[str]] = None,
        beta: Optional[float] = None
    ) -> Tuple[float, Dict]:
        """
        Calculate weighted technical score using TECHNICAL_WEIGHTS from config.

        Args:
            df: OHLCV DataFrame
            selected_components: List of components to include (e.g., ['moving_averages', 'momentum', ...])
                                Default None = all 5 components
            beta: Market sensitivity coefficient (optional, for volatility adjustment)

        Returns:
            Tuple of (overall_score, component_scores_dict)
        """
        try:
            # Calculate all component scores
            ma_score = self.calculate_moving_average_score(df)
            momentum_score = self.calculate_momentum_score(df)
            volatility_score = self.calculate_volatility_score(df, beta=beta)
            volume_flow_score, vf_detail = self.calculate_volume_flow_score(df)
            fib_score = self.calculate_fibonacci_score(df)
            ichimoku_score = self.calculate_ichimoku_score(df)

            all_scores = {
                'moving_averages': ma_score,
                'momentum': momentum_score,
                'volatility': volatility_score,
                'volume_flow': volume_flow_score,
                'fibonacci': fib_score,
                'ichimoku': ichimoku_score,
            }

            # Determine active components (default = all 5)
            active = selected_components or list(self.weights.keys())

            # Recalculate weights sum for normalization if subset is selected
            active_weights = {k: self.weights[k] for k in active if k in self.weights}
            active_weight_sum = sum(active_weights.values()) or 1.0

            # Calculate weighted score using only active components
            overall_score = sum(
                all_scores[k] * (self.weights[k] / active_weight_sum)
                for k in active
                if k in all_scores
            )

            # Component scores dict (includes volume_flow details)
            component_scores = {
                'moving_averages': round(ma_score, 1),
                'momentum': round(momentum_score, 1),
                'volatility': round(volatility_score, 1),
                'volume_flow': round(volume_flow_score, 1),
                'volume_flow_detail': vf_detail,
                'fibonacci': round(fib_score, 1),
                'ichimoku': round(ichimoku_score, 1),
            }

            return round(overall_score, 1), component_scores

        except Exception as e:
            logger.error(f"Error calculating overall technical score: {e}")
            return 50.0, {}


# Convenience function
def calculate_technical_score(df: pd.DataFrame) -> float:
    """Quick technical score calculation."""
    calculator = TechnicalScoreCalculator()
    score, _ = calculator.calculate_overall_technical_score(df)
    return score
