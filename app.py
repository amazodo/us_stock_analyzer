"""Streamlit web app for US Stock AI Analyzer - Updated with Latest Logic."""

import logging
import streamlit as st
from datetime import datetime
import sys

from config.settings import LOGS_DIR

# Suppress warnings
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

from src.pipeline import AnalysisPipeline
from src.collectors.news_data import NewsDataCollector
from src.ui.views import render_summary_view, render_detail_view

# Configure logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "streamlit.log"),
    ]
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="US Stock AI Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.markdown("# 📊 US Stock AI Analyzer")
st.markdown("**기술적 지표 기반 Top 5 종목 추천 시스템** (실시간 뉴스 통합)")
st.markdown("---")

# Sidebar controls
with st.sidebar:
    st.markdown("## ⚙️ 분석 설정")

    analysis_period = st.selectbox(
        "분석 기간",
        options=[
            ("1개월", 30),
            ("3개월", 90),
            ("6개월", 180),
            ("1년", 365),
        ],
        index=3,
        key="period_select"
    )

    period_days = analysis_period[1]

    st.markdown("---")
    st.markdown("### 📋 기술 지표 (6개)")
    st.info("""
    - **이동평균** (24%) - SMA/EMA 추세
    - **모멘텀** (16%) - RSI/MACD/Stochastic
    - **변동성** (16%) - Bollinger Bands/ATR
    - **거래량/수급** (16%) - OBV/VWAP/MFI
    - **피보나치** (8%) - 지지/저항선
    - **일목균형표** (20%) - Kumo/전환선/기준선
    """)

    st.markdown("---")
    st.markdown("### 🎯 분석 목표")
    st.text("5% 상승률을 1주일 내 달성할 수 있는 종목")

    st.markdown("---")

    run_analysis = st.button(
        "🚀 분석 시작",
        use_container_width=True,
        type="primary"
    )

# Main content
if run_analysis:
    with st.spinner("🔄 분석 중... (3-10분 소요)"):
        try:
            # Step 1: Run pipeline analysis
            logger.info(f"Starting analysis with {period_days} days period")
            pipeline = AnalysisPipeline(period_days=period_days)
            results = pipeline.run_full_analysis()

            # Step 2: Fetch news for top 5
            logger.info("Fetching news for top 5 stocks")
            ranking_report = results.get('ranking_report', {})
            top_stocks = ranking_report.get('recommendations', [])[:5]

            news_collector = NewsDataCollector()
            news_data = {}
            for stock in top_stocks:
                ticker = stock.get('ticker')
                try:
                    articles = news_collector.search_ticker_news(ticker, period_days=30)
                    if articles:
                        news_data[ticker] = articles
                except Exception as e:
                    logger.debug(f"Could not fetch news for {ticker}: {e}")

            logger.info(f"Fetched news for {len(news_data)}/{len(top_stocks)} stocks")

            # Store in session state
            st.session_state['results'] = results
            st.session_state['news_data'] = news_data
            st.session_state['timestamp'] = datetime.now().isoformat()

            st.success("✅ 분석 완료! 아래에서 결과를 확인하세요.")

        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            st.error(f"❌ 분석 실패: {str(e)}")
            st.info("문제가 지속되면 GitHub 이슈를 등록해주세요.")

# Display results if available
if 'results' in st.session_state:
    results = st.session_state['results']
    news_data = st.session_state.get('news_data', {})

    # Summary view
    render_summary_view(results)

    st.markdown("---")

    # Top 5 stocks with news
    st.markdown("## 🏆 Top 5 추천 종목")

    ranking_report = results.get('ranking_report', {})
    top_stocks = ranking_report.get('recommendations', [])[:5]

    for rank, stock in enumerate(top_stocks, 1):
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 2])

            with col1:
                st.markdown(f"### #{rank}")

            with col2:
                ticker = stock.get('ticker', 'N/A')
                overall = stock.get('overall_score', 0)
                tech = stock.get('technical_score', 0)

                st.markdown(f"**{ticker}**")
                st.metric("종합 점수", f"{overall:.1f}/100", delta=None)
                st.metric("기술 점수", f"{tech:.1f}/100", delta=None)

            with col3:
                # News section
                if ticker in news_data:
                    articles = news_data[ticker]
                    st.markdown("**최신 뉴스**")
                    for i, article in enumerate(articles[:3], 1):
                        title = article.get('title', 'No title')
                        url = article.get('url', '')
                        if url:
                            st.markdown(f"{i}. [{title[:60]}...]({url})")
                        else:
                            st.text(f"{i}. {title[:60]}...")
                else:
                    st.markdown("**뉴스**")
                    st.text("뉴스 정보 미제공")

            st.markdown("---")

    st.markdown("---")

    # Detailed analysis view
    render_detail_view(results, news_data)

    st.markdown("---")

    # Export options
    st.markdown("## 📥 보고서 내보내기")

    col1, col2 = st.columns(2)

    with col1:
        # Markdown report
        report_text = f"""
# 📊 Weekly Top 5 Stock Recommendations

**분석 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**분석 기간**: {period_days}일
**대상**: S&P 100

## 🏆 Top 5 추천 종목

"""
        for rank, stock in enumerate(top_stocks, 1):
            ticker = stock.get('ticker', 'N/A')
            overall = stock.get('overall_score', 0)
            tech = stock.get('technical_score', 0)

            report_text += f"""
### #{rank}. {ticker}
- **종합 점수**: {overall:.1f}/100
- **기술 점수**: {tech:.1f}/100
- **목표**: 1주일 내 5% 상승

"""
            if ticker in news_data:
                report_text += f"**최신 뉴스**:\n"
                for article in news_data[ticker][:3]:
                    title = article.get('title', 'N/A')
                    url = article.get('url', '')
                    report_text += f"- [{title}]({url})\n"
                report_text += "\n"

        st.download_button(
            label="📄 마크다운 리포트 다운로드",
            data=report_text,
            file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )

    with col2:
        # JSON export
        import json
        json_data = json.dumps(results, indent=2, default=str)
        st.download_button(
            label="📊 JSON 데이터 내보내기",
            data=json_data,
            file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

else:
    # Welcome message
    st.markdown("""
    ## 👋 시작하기

    왼쪽 사이드바에서 **분석 기간**을 선택하고 **🚀 분석 시작** 버튼을 클릭하세요.

    ### 📊 분석 기능
    - **6개 기술 지표**: 이동평균, 모멘텀, 변동성, 거래량, 피보나치, 일목균형표
    - **실시간 뉴스**: 각 종목별 최신 뉴스 링크
    - **섹터 모멘텀**: 업종별 상대 강도 분석
    - **실적 리스크**: 실적 발표 일정 확인
    - **ATR 필터**: 변동성 기반 가능성 검증

    ### 🎯 목표
    5% 상승 가능성이 높은 Top 5 종목을 추천합니다 (1주일 기준)

    ### ⚙️ 기술 스택
    - **데이터**: yfinance, NewsAPI
    - **분석**: pandas, ta (Technical Analysis)
    - **UI**: Streamlit
    - **배포**: GitHub + Streamlit Cloud
    """)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #999; font-size: 11px; margin-top: 2rem;'>
    <p>📈 US Stock AI Analyzer | 기술적 지표 기반 분석</p>
    <p>⚠️ 본 분석은 정보 제공용이며 투자 조언이 아닙니다</p>
    <p>💼 항상 자신의 판단과 전문가 자문으로 투자 결정하세요</p>
    <p style='font-size: 10px; margin-top: 1rem;'>GitHub: <a href='https://github.com/your-username/us-stock-analyzer' target='_blank'>us-stock-analyzer</a></p>
    </div>
""", unsafe_allow_html=True)
