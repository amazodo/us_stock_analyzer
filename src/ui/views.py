"""Streamlit view components for displaying analysis results."""

import logging
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional

from src.ui.charts import build_candlestick_chart
from src.collectors.stock_data import StockDataCollector

logger = logging.getLogger(__name__)


def render_summary_view(results: Dict) -> None:
    """
    Render summary dashboard with Top 5 metric cards and market regime badge.

    Args:
        results: Analysis results dict from pipeline
    """
    st.markdown("## 📊 Top 5 추천 요약")
    st.markdown("---")

    # Get top 5 from ranking report
    ranking_report = results.get('ranking_report', {})
    top_stocks = ranking_report.get('recommendations', [])[:5]

    if not top_stocks:
        st.warning("No recommendations available")
        return

    # Display market regime badge (from pipeline calculation)
    market_regime = results.get('market_regime', {})
    regime_type = market_regime.get('regime', 'unknown').upper()
    regime_desc = market_regime.get('description', 'Market regime unavailable')

    # Color based on regime
    if regime_type == 'SAFE':
        regime_color = "green"
        regime_emoji = "🟢"
    elif regime_type == 'CAUTION':
        regime_color = "orange"
        regime_emoji = "🟡"
    elif regime_type == 'RISK_OFF':
        regime_color = "red"
        regime_emoji = "🔴"
    else:
        regime_color = "gray"
        regime_emoji = "⚫"

    st.markdown(f"<div style='text-align: center; font-size: 18px; color: {regime_color};'><b>{regime_emoji} {regime_type}</b></div>",
               unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 12px; color: {regime_color};'>{regime_desc}</div>",
               unsafe_allow_html=True)

    st.markdown("---")

    # Display Top 5 as metric cards with latest factors
    sector_map = results.get('sector_map', {})
    sector_bonuses = results.get('sector_bonuses', {})
    earnings_risk = results.get('earnings_risk_data', {})

    cols = st.columns(5)

    for idx, (col, stock) in enumerate(zip(cols, top_stocks)):
        with col:
            ticker = stock.get('ticker', 'N/A')
            overall_score = stock.get('overall_score', 0)
            tech_score = stock.get('technical_score', 0)
            sentiment_score = stock.get('sentiment_score', 0)

            # Sector info
            sector = sector_map.get(ticker, 'N/A')
            sector_bonus = sector_bonuses.get(ticker, 0.0)

            # Earnings risk
            earnings_data = earnings_risk.get(ticker, {})
            has_earnings_risk = earnings_data.get('within_risk_window', False)

            # Build help text with all factors
            help_text = f"Sector: {sector}"
            if sector_bonus != 0:
                help_text += f"\nSector Bonus: {sector_bonus:+.1f}"
            help_text += f"\nTech: {tech_score:.0f}, Sentiment: {sentiment_score:.0f}"
            if has_earnings_risk:
                earnings_date = earnings_data.get('next_earnings_date', 'N/A')
                help_text += f"\n⚠️ Earnings: {earnings_date}"

            st.metric(
                label=f"#{idx+1}. {ticker}",
                value=f"{overall_score:.1f}",
                help=help_text
            )

    st.markdown("---")

    # Statistics
    score_dist = ranking_report.get('score_distribution', {})
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("평균 점수", f"{score_dist.get('mean', 0):.1f}")
    with col2:
        st.metric("최고 점수", f"{score_dist.get('max', 0):.1f}")
    with col3:
        st.metric("분석 종목", f"{score_dist.get('count', 0)}")

    # ATR Filter info
    excluded = results.get('excluded_by_atr_filter', [])
    if excluded:
        with st.expander(f"⚠️ ATR 필터링 제외 ({len(excluded)}개)"):
            for item in excluded:
                ticker = item.get('ticker', 'N/A')
                reason = item.get('reason', 'Unknown')
                st.text(f"• {ticker}: {reason}")


def render_detail_view(results: Dict, news_data: Dict = None) -> None:
    """
    Render detailed view with per-stock analysis (charts, scores, news).

    Args:
        results: Analysis results dict from pipeline
        news_data: News articles per ticker
    """
    if news_data is None:
        news_data = {}
    st.markdown("## 📈 종목별 상세 분석")
    st.markdown("---")

    # Get top 5 tickers
    ranking_report = results.get('ranking_report', {})
    top_stocks = ranking_report.get('recommendations', [])[:5]

    if not top_stocks:
        st.warning("No stock data for detailed analysis")
        return

    tickers = [s.get('ticker', 'N/A') for s in top_stocks]

    # Ticker selection
    selected_ticker = st.selectbox("종목 선택", tickers, key="ticker_selector")

    # Get stock data
    stock_data = results.get('stock_data', {})
    df = stock_data.get(selected_ticker)

    if df is None or len(df) == 0:
        st.error(f"No data available for {selected_ticker}")
        return

    # Tabs for different analysis sections
    tab1, tab2, tab3 = st.tabs(["📊 차트", "📈 점수분석", "📰 뉴스"])

    with tab1:
        st.markdown(f"### {selected_ticker} - 기술 차트")

        # Timeframe selector
        col1, col2 = st.columns([2, 1])
        with col1:
            overlays = st.multiselect(
                "오버레이 추가",
                options=['sma20', 'sma50', 'sma200', 'bollinger', 'vwap', 'ichimoku'],
                default=['sma20', 'sma50'],
                key=f"overlays_{selected_ticker}"
            )
        with col2:
            timeframe = st.radio("시간틀", options=['1D', '1W', '1M'], horizontal=True)

        # Sub-chart selector
        sub_chart = st.radio("보조 지표", options=['volume', 'macd', 'rsi', 'obv'], horizontal=True)

        # Build and display chart
        fig = build_candlestick_chart(df, selected_ticker, overlays, sub_chart, timeframe)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown(f"### {selected_ticker} - 점수 분석")

        # Find stock in top 5
        stock_info = next((s for s in top_stocks if s.get('ticker') == selected_ticker), None)

        if stock_info:
            # Main scores
            col1, col2 = st.columns(2)
            with col1:
                st.metric("종합 점수", f"{stock_info.get('overall_score', 0):.1f}/100")
            with col2:
                st.metric("기술 점수", f"{stock_info.get('technical_score', 0):.1f}/100")

            st.markdown("---")

            # Latest factors
            sector_map = results.get('sector_map', {})
            sector_bonuses = results.get('sector_bonuses', {})
            earnings_risk = results.get('earnings_risk_data', {})

            col1, col2, col3 = st.columns(3)
            with col1:
                sector = sector_map.get(selected_ticker, 'N/A')
                sector_bonus = sector_bonuses.get(selected_ticker, 0.0)
                st.metric("섹터", sector)
                st.metric("섹터 보너스", f"{sector_bonus:+.1f}점")

            with col2:
                earnings_data = earnings_risk.get(selected_ticker, {})
                if earnings_data.get('within_risk_window', False):
                    st.warning(f"⚠️ 실적 임박: {earnings_data.get('next_earnings_date', 'N/A')}")
                    st.metric("실적 감점", f"-{5.0:.1f}점")
                else:
                    st.success("✓ 실적 리스크 없음")

            with col3:
                market_regime = results.get('market_regime', {})
                regime = market_regime.get('regime', 'unknown').upper()
                st.metric("시장 레짐", regime)

            # Risk/Reward
            current_price = df['Close'].iloc[-1]
            target_price = current_price * 1.05
            stop_loss = current_price * 0.95

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("현재가", f"${current_price:.2f}")
            with col2:
                st.metric("목표가 (+5%)", f"${target_price:.2f}")
            with col3:
                st.metric("손절가 (-5%)", f"${stop_loss:.2f}")

            # Risk/Reward Ratio
            reward = target_price - current_price
            risk = current_price - stop_loss
            if risk > 0:
                rr_ratio = reward / risk
                st.markdown(f"**손익비**: {rr_ratio:.2f}:1 {'✅' if rr_ratio >= 2 else '⚠️'}")

            # Earnings warning
            if stock_info.get('earnings_warning'):
                st.warning(f"⚠️ 실적 발표 예정: {stock_info.get('next_earnings_date', 'TBD')}")

        else:
            st.info("No score information available for this stock")

    with tab3:
        st.markdown(f"### {selected_ticker} - 최신 뉴스")

        news_data = results.get('news_data', {})
        articles = news_data.get(selected_ticker, [])

        if articles:
            for idx, article in enumerate(articles[:5]):  # Show top 5 articles
                title = article.get('title', 'No title')
                url = article.get('url', '')
                source = article.get('source', 'Unknown')
                date = article.get('published_at', '')

                # Display title as clickable link
                if url:
                    st.markdown(f"**{idx+1}. [{title}]({url})**")
                else:
                    st.markdown(f"**{idx+1}. {title}**")

                st.markdown(f"*{source} - {date}*")

                desc = article.get('description', '')
                if desc:
                    st.markdown(f"<small>{desc[:200]}...</small>", unsafe_allow_html=True)

                st.markdown("---")

        else:
            st.info("No recent news available for this stock")
