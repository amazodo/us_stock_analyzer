"""Plotly chart components for stock analysis."""

import logging
from typing import List, Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


def build_candlestick_chart(
    df: pd.DataFrame,
    ticker: str = "TICKER",
    overlays: Optional[List[str]] = None,
    sub_chart: str = "volume",
    timeframe: str = "1D"
) -> go.Figure:
    """
    Build an interactive candlestick chart with technical overlays.

    Args:
        df: OHLCV DataFrame with columns: Open, High, Low, Close, Volume
        ticker: Stock ticker for title
        overlays: List of overlays to include (e.g., ['sma20', 'sma50', 'bollinger', 'vwap', 'fibonacci'])
        sub_chart: Subplot type ('volume', 'macd', 'rsi', 'obv')
        timeframe: Timeframe label ('1D', '1W', '1M')

    Returns:
        Plotly Figure object
    """
    try:
        # Resample data based on timeframe
        df_plot = df.copy()
        if timeframe == '1W':
            df_plot = df_plot.resample('W').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
        elif timeframe == '1M':
            df_plot = df_plot.resample('M').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()

        # Create subplots (main chart + sub-indicator)
        rows = 2 if sub_chart in ['volume', 'macd', 'rsi', 'obv'] else 1
        row_heights = [0.7, 0.3] if rows == 2 else [1]

        fig = make_subplots(
            rows=rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights
        )

        # Main candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df_plot.index,
                open=df_plot['Open'],
                high=df_plot['High'],
                low=df_plot['Low'],
                close=df_plot['Close'],
                name='OHLC'
            ),
            row=1, col=1
        )

        # Add technical overlays
        overlays = overlays or []

        if 'sma20' in overlays and 'SMA_20' in df_plot.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_plot.index,
                    y=df_plot['SMA_20'],
                    mode='lines',
                    name='SMA 20',
                    line=dict(color='orange', width=1)
                ),
                row=1, col=1
            )

        if 'sma50' in overlays and 'SMA_50' in df_plot.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_plot.index,
                    y=df_plot['SMA_50'],
                    mode='lines',
                    name='SMA 50',
                    line=dict(color='blue', width=1)
                ),
                row=1, col=1
            )

        if 'sma200' in overlays and 'SMA_200' in df_plot.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_plot.index,
                    y=df_plot['SMA_200'],
                    mode='lines',
                    name='SMA 200',
                    line=dict(color='red', width=1)
                ),
                row=1, col=1
            )

        if 'bollinger' in overlays and 'BB_Upper' in df_plot.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_plot.index,
                    y=df_plot['BB_Upper'],
                    mode='lines',
                    name='BB Upper',
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df_plot.index,
                    y=df_plot['BB_Lower'],
                    mode='lines',
                    name='BB Lower',
                    line=dict(color='rgba(0,0,0,0)'),
                    fill='tonexty',
                    fillcolor='rgba(0,100,200,0.1)',
                    showlegend=False
                ),
                row=1, col=1
            )

        if 'vwap' in overlays and 'VWAP' in df_plot.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_plot.index,
                    y=df_plot['VWAP'],
                    mode='lines',
                    name='VWAP',
                    line=dict(color='purple', width=1, dash='dash')
                ),
                row=1, col=1
            )

        # Ichimoku Cloud overlay
        if 'ichimoku' in overlays:
            # Calculate Ichimoku if not already present
            if 'Ichimoku_Tenkan' not in df_plot.columns:
                try:
                    from src.indicators.ichimoku import IchimokuIndicators
                    df_plot = IchimokuIndicators.calculate_ichimoku(df_plot)
                except Exception as e:
                    logger.warning(f"Failed to calculate Ichimoku: {e}")

            # Add Tenkan-sen (Conversion Line)
            if 'Ichimoku_Tenkan' in df_plot.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_plot.index,
                        y=df_plot['Ichimoku_Tenkan'],
                        mode='lines',
                        name='Tenkan-sen',
                        line=dict(color='red', width=1)
                    ),
                    row=1, col=1
                )

            # Add Kijun-sen (Base Line)
            if 'Ichimoku_Kijun' in df_plot.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_plot.index,
                        y=df_plot['Ichimoku_Kijun'],
                        mode='lines',
                        name='Kijun-sen',
                        line=dict(color='blue', width=1)
                    ),
                    row=1, col=1
                )

            # Add Senkou Span A (upper cloud)
            if 'Ichimoku_SenkouA' in df_plot.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_plot.index,
                        y=df_plot['Ichimoku_SenkouA'],
                        mode='lines',
                        name='Senkou Span A',
                        line=dict(color='rgba(0,200,0,0.3)', width=0.5),
                        showlegend=False
                    ),
                    row=1, col=1
                )

            # Add Senkou Span B (lower cloud) with fill
            if 'Ichimoku_SenkouB' in df_plot.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_plot.index,
                        y=df_plot['Ichimoku_SenkouB'],
                        mode='lines',
                        name='Senkou Span B',
                        line=dict(color='rgba(200,0,0,0.3)', width=0.5),
                        fill='tonexty',
                        fillcolor='rgba(100,100,100,0.1)',
                        showlegend=False
                    ),
                    row=1, col=1
                )

        # Sub-chart (Volume, MACD, RSI, OBV)
        if rows == 2:
            if sub_chart == 'volume':
                colors = ['red' if df_plot['Close'].iloc[i] < df_plot['Open'].iloc[i] else 'green'
                          for i in range(len(df_plot))]
                fig.add_trace(
                    go.Bar(
                        x=df_plot.index,
                        y=df_plot['Volume'],
                        name='Volume',
                        marker_color=colors,
                        showlegend=False
                    ),
                    row=2, col=1
                )

            elif sub_chart == 'macd' and 'MACD' in df_plot.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_plot.index,
                        y=df_plot['MACD'],
                        mode='lines',
                        name='MACD',
                        line=dict(color='blue', width=1)
                    ),
                    row=2, col=1
                )
                if 'MACD_Signal' in df_plot.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df_plot.index,
                            y=df_plot['MACD_Signal'],
                            mode='lines',
                            name='Signal',
                            line=dict(color='red', width=1)
                        ),
                        row=2, col=1
                    )

            elif sub_chart == 'rsi' and 'RSI_14' in df_plot.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_plot.index,
                        y=df_plot['RSI_14'],
                        mode='lines',
                        name='RSI 14',
                        line=dict(color='green', width=1)
                    ),
                    row=2, col=1
                )
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, annotation_text="Overbought")
                fig.add_hline(y=30, line_dash="dash", line_color="blue", row=2, annotation_text="Oversold")

            elif sub_chart == 'obv' and 'OBV' in df_plot.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_plot.index,
                        y=df_plot['OBV'],
                        mode='lines',
                        name='OBV',
                        line=dict(color='purple', width=1)
                    ),
                    row=2, col=1
                )

        # Update layout
        fig.update_layout(
            title=f"{ticker} - {timeframe} Chart",
            xaxis_rangeslider_visible=False,
            template='plotly_white',
            height=500,
            hovermode='x unified'
        )

        return fig

    except Exception as e:
        logger.error(f"Error building candlestick chart: {e}")
        # Return empty figure
        fig = go.Figure()
        fig.add_annotation(text="Failed to generate chart")
        return fig
