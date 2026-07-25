"""Streamlit sidebar controls for analysis parameters."""

import streamlit as st
from typing import Dict, List

from config.settings import (
    HISTORY_MONTHS_DEFAULT, HISTORY_MONTHS_MIN, HISTORY_MONTHS_MAX
)


def render_sidebar() -> Dict:
    """
    Render sidebar with analysis controls.

    Returns:
        Dictionary with:
          - 'months': int (history period in months)
          - 'selected_components': List[str] (selected technical indicators)
          - 'include_sentiment': bool
          - 'include_sector_momentum': bool
          - 'run_clicked': bool (Run Analysis button clicked)
    """
    st.sidebar.markdown("## ⚙️ 분석 설정")
    st.sidebar.markdown("---")

    # History Period Slider
    st.sidebar.markdown("### 📅 분석 기간")
    months = st.sidebar.slider(
        "분석 기간 (개월)",
        min_value=HISTORY_MONTHS_MIN,
        max_value=HISTORY_MONTHS_MAX,
        value=HISTORY_MONTHS_DEFAULT,
        step=1,
        help="과거 몇 개월의 데이터로 분석할까요?"
    )

    st.sidebar.markdown("---")

    # Technical Indicators Multi-select
    st.sidebar.markdown("### 📊 기술적 지표")
    st.sidebar.markdown("*(분석에 포함할 지표 선택)*")

    # Define indicator options with their descriptions
    indicators = {
        'moving_averages': '📈 이동평균선 (SMA/EMA)',
        'momentum': '⚡ 모멘텀 지표 (RSI/MACD)',
        'volatility': '📉 변동성 지표 (BB/ATR)',
        'volume_flow': '💧 거래량 & 수급 (OBV/VWAP)',
        'fibonacci': '🔄 피보나치 되돌림'
    }

    selected_components = []
    for key, label in indicators.items():
        if st.sidebar.checkbox(label, value=True, key=f"cb_{key}"):
            selected_components.append(key)

    st.sidebar.markdown("---")

    # Analysis Methods
    st.sidebar.markdown("### 📰 분석 방법")

    include_sentiment = st.sidebar.checkbox(
        "💬 뉴스 감성 분석",
        value=True,
        help="거시경제/종목별 뉴스와 전문가 의견 포함"
    )

    include_sector_momentum = st.sidebar.checkbox(
        "🏭 섹터 모멘텀",
        value=True,
        help="섹터 상대 강도 분석 포함"
    )

    st.sidebar.markdown("---")

    # Run Analysis Button
    st.sidebar.markdown("### 🚀 분석 실행")
    run_clicked = st.sidebar.button(
        "분석 시작",
        type="primary",
        use_container_width=True,
        help="새로운 분석을 실행합니다"
    )

    st.sidebar.markdown("---")

    # Footer
    st.sidebar.markdown("### ℹ️ 정보")
    st.sidebar.markdown(
        """
        **US Stock AI Analyzer**
        기술적 지표 + 감성 분석 + 전문가 의견
        을 통한 Top 5 종목 추천

        **주의**: 이 분석은 정보 제공용이며
        투자 조언이 아닙니다.
        """
    )

    return {
        'months': months,
        'selected_components': selected_components,
        'include_sentiment': include_sentiment,
        'include_sector_momentum': include_sector_momentum,
        'run_clicked': run_clicked
    }
