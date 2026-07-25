"""Streamlit app - US Stock AI Analyzer."""

import logging
import streamlit as st
from datetime import datetime
import json

logging.getLogger('yfinance').setLevel(logging.CRITICAL)

from config.settings import LOGS_DIR
from src.pipeline import AnalysisPipeline
from src.collectors.news_data import NewsDataCollector

LOGS_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="US Stock AI Analyzer", page_icon="📈", layout="wide")

# CSS styling
st.markdown("""
<style>
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📊 US Stock AI Analyzer")
st.markdown("**기술적 지표 기반 Top 5 종목 추천**")
st.markdown("---")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'news_data' not in st.session_state:
    st.session_state['news_data'] = {}
if 'last_analysis' not in st.session_state:
    st.session_state['last_analysis'] = None

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ 분석 설정")

    period_options = [("1개월", 30), ("3개월", 90), ("6개월", 180), ("1년", 365)]
    selected = st.selectbox("분석 기간", period_options, index=3)
    period_days = selected[1]

    st.markdown("---")
    st.info("6개 지표: 이동평균 • 모멘텀 • 변동성 • 거래량 • 피보나치 • 일목균형표")

    run_button = st.button("🚀 분석 시작", use_container_width=True, type="primary", key="run_button")

# Function to fetch news
def fetch_news_for_stocks(top_stocks, period_days=30):
    """Fetch news for top stocks with error handling."""
    news_data = {}
    news_collector = NewsDataCollector()

    for idx, stock in enumerate(top_stocks):
        ticker = stock.get('ticker')
        try:
            articles = news_collector.search_ticker_news(ticker, period_days=period_days)
            if articles:
                news_data[ticker] = articles
                logger.info(f"Fetched {len(articles)} articles for {ticker}")
        except Exception as e:
            logger.debug(f"News fetch failed for {ticker}: {e}")

    return news_data

# Run analysis if button clicked
if run_button:
    progress_container = st.container()

    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("🔄 분석 초기화 중...")
            progress_bar.progress(10)
            logger.info(f"Starting analysis: {period_days} days")

            # Initialize pipeline
            pipeline = AnalysisPipeline(period_days=period_days)
            logger.info("Pipeline initialized")

            status_text.text("📊 데이터 수집 중...")
            progress_bar.progress(30)

            # Run analysis
            results = pipeline.run_full_analysis()
            logger.info(f"Pipeline returned: {type(results)}")

            progress_bar.progress(60)

            if not results or 'ranking_report' not in results:
                logger.error(f"Invalid results: {type(results)}")
                st.error("❌ 분석 실패: 결과가 없습니다. 다시 시도하세요.")
                st.stop()

            # Extract recommendations
            ranking_report = results.get('ranking_report', {})
            recommendations = ranking_report.get('recommendations', [])

            if not recommendations:
                logger.error(f"No recommendations in ranking_report")
                st.error("❌ 추천 종목을 찾을 수 없습니다. 나중에 다시 시도하세요.")
                st.stop()

            top_stocks = recommendations[:5]
            logger.info(f"Found {len(top_stocks)} top stocks")

            # Store in session
            st.session_state['results'] = results
            st.session_state['last_analysis'] = datetime.now().isoformat()

            status_text.text("📰 뉴스 수집 중...")
            progress_bar.progress(80)

            # Fetch news
            news_data = fetch_news_for_stocks(top_stocks, period_days=30)
            st.session_state['news_data'] = news_data

            progress_bar.progress(100)
            status_text.text(f"✅ 완료! ({len(top_stocks)} 종목, 뉴스: {len(news_data)})")

            logger.info(f"Analysis complete: {len(top_stocks)} stocks, {len(news_data)} with news")

            # Force rerun to display results
            st.rerun()

        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            st.error(f"❌ 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            st.stop()

# Display results
if st.session_state.get('results'):
    results = st.session_state['results']
    news_data = st.session_state.get('news_data', {})

    # Extract data
    ranking_report = results.get('ranking_report', {})
    recommendations = ranking_report.get('recommendations', [])
    top_stocks = recommendations[:5] if recommendations else []

    if not top_stocks:
        st.warning("⚠️ 추천 종목이 없습니다.")
    else:
        # Display timestamp
        analysis_time = st.session_state.get('last_analysis', 'Unknown')
        st.caption(f"분석 시간: {analysis_time}")

        # Summary cards
        st.markdown("## 📊 Top 5 추천 요약")

        for rank, stock in enumerate(top_stocks, 1):
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([0.5, 1, 1.5, 2])

                ticker = stock.get('ticker', 'N/A')
                overall = float(stock.get('overall_score', 0))
                tech = float(stock.get('technical_score', 0))

                with col1:
                    st.metric("", f"#{rank}", label_visibility="collapsed")

                with col2:
                    st.subheader(ticker)

                with col3:
                    st.metric("종합점수", f"{overall:.1f}", delta=f"기술: {tech:.1f}")

                with col4:
                    if ticker in news_data:
                        articles = news_data[ticker][:2]
                        st.markdown("**최신 뉴스:**")
                        for i, article in enumerate(articles, 1):
                            title = article.get('title', '')[:45]
                            url = article.get('url', '')
                            if url:
                                st.markdown(f"[{i}. {title}...](${url})")
                    else:
                        st.text("뉴스 없음")

        # Statistics
        with st.expander("📈 분석 통계"):
            col1, col2, col3 = st.columns(3)

            dist = ranking_report.get('score_distribution', {})
            with col1:
                st.metric("평균 점수", f"{dist.get('mean', 0):.1f}/100")
            with col2:
                st.metric("최대 점수", f"{dist.get('max', 0):.1f}/100")
            with col3:
                st.metric("최소 점수", f"{dist.get('min', 0):.1f}/100")

        # Export section
        st.markdown("---")
        st.markdown("## 📥 다운로드")

        col1, col2 = st.columns(2)

        with col1:
            json_str = json.dumps(results, indent=2, default=str)
            st.download_button(
                "📋 JSON",
                json_str,
                f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json"
            )

        with col2:
            report = "# Top 5 Recommendations\n\n"
            report += f"Analysis Date: {st.session_state.get('last_analysis', 'Unknown')}\n\n"
            for rank, stock in enumerate(top_stocks, 1):
                ticker = stock.get('ticker')
                overall = stock.get('overall_score', 0)
                tech = stock.get('technical_score', 0)
                report += f"{rank}. **{ticker}**\n"
                report += f"   - Overall: {overall:.1f}/100\n"
                report += f"   - Technical: {tech:.1f}/100\n\n"

            st.download_button(
                "📄 텍스트",
                report,
                f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain"
            )

else:
    # Welcome message
    st.info("""
    ### 👋 시작하기

    좌측 사이드바에서 분석 기간을 선택하고 **🚀 분석 시작** 버튼을 누르세요.

    **기능:**
    - ✅ 6개 기술 지표 분석 (이동평균, 모멘텀, 변동성, 거래량, 피보나치, 일목균형표)
    - ✅ 실시간 뉴스 통합
    - ✅ 자동 리포트 생성

    **처음 사용하시나요?**
    분석은 첫 실행 시 3-10분 정도 소요됩니다. 기간을 선택하고 분석 시작 버튼을 누르세요.

    **팁:**
    - 기간을 길게 설정할수록 더 많은 데이터를 분석합니다
    - 분석 결과는 여러 번 조회할 수 있습니다
    - 다시 분석 시작을 누르면 새로운 분석이 시작됩니다
    """)

st.markdown("---")
st.caption("⚠️ 정보 제공용이며 투자 조언이 아닙니다.")
