"""Streamlit app - US Stock AI Analyzer."""

import logging
import streamlit as st
from datetime import datetime

logging.getLogger('yfinance').setLevel(logging.CRITICAL)

from config.settings import LOGS_DIR
from src.pipeline import AnalysisPipeline
from src.collectors.news_data import NewsDataCollector

LOGS_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="US Stock AI Analyzer", page_icon="📈", layout="wide")

st.markdown("# 📊 US Stock AI Analyzer")
st.markdown("**기술적 지표 기반 Top 5 종목 추천**")
st.markdown("---")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'news_data' not in st.session_state:
    st.session_state['news_data'] = {}

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ 분석 설정")
    
    period_options = [("1개월", 30), ("3개월", 90), ("6개월", 180), ("1년", 365)]
    selected = st.selectbox("분석 기간", period_options, index=3)
    period_days = selected[1]
    
    st.markdown("---")
    st.info("6개 지표: 이동평균 • 모멘텀 • 변동성 • 거래량 • 피보나치 • 일목균형표")
    
    run_button = st.button("🚀 분석 시작", use_container_width=True, type="primary")

# Main - Run analysis if button clicked
if run_button:
    with st.spinner("🔄 분석 중... (3-10분)"):
        try:
            logger.info(f"Starting analysis: {period_days} days")

            # Initialize pipeline
            pipeline = AnalysisPipeline(period_days=period_days)
            logger.info("Pipeline initialized")

            # Run analysis
            results = pipeline.run_full_analysis()
            logger.info(f"Pipeline returned: {type(results)}")

            if not results:
                logger.error("Pipeline returned None or empty results")
                st.error("분석 실패: 결과가 없습니다.")
                st.stop()

            # Validate ranking_report
            ranking_report = results.get('ranking_report', {})
            if not ranking_report:
                logger.error(f"No ranking_report. Keys: {list(results.keys())}")
                st.error("분석 결과가 없습니다.")
                st.stop()

            top_stocks = ranking_report.get('recommendations', [])
            if not top_stocks:
                logger.error(f"No recommendations. Keys: {list(ranking_report.keys())}")
                st.error("추천 종목이 없습니다.")
                st.stop()

            top_stocks = top_stocks[:5]
            logger.info(f"Found {len(top_stocks)} top stocks")

            # Store in session
            st.session_state['results'] = results

            # Fetch news
            news_data = {}
            news_collector = NewsDataCollector()
            for stock in top_stocks:
                ticker = stock.get('ticker')
                try:
                    articles = news_collector.search_ticker_news(ticker, period_days=30)
                    if articles:
                        news_data[ticker] = articles
                except Exception as ne:
                    logger.debug(f"News fetch failed for {ticker}: {ne}")
                    pass

            st.session_state['news_data'] = news_data
            logger.info(f"Fetched news for {len(news_data)}/{len(top_stocks)} stocks")

            # Success
            st.success(f"✅ 완료! ({len(top_stocks)} 종목 분석, 뉴스: {len(news_data)})")

        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            st.error(f"❌ 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

# Display results
if st.session_state.get('results'):
    results = st.session_state['results']
    news_data = st.session_state.get('news_data', {})

    # Validate and extract
    ranking_report = results.get('ranking_report')
    if not ranking_report:
        st.error("⚠️ 분석 결과가 손상되었습니다. 다시 시도하세요.")
        logger.error(f"Results keys: {list(results.keys())}")
    else:
        recommendations = ranking_report.get('recommendations', [])
        if not recommendations:
            st.error("⚠️ 추천 종목이 없습니다. 데이터를 다시 확인하세요.")
            logger.error(f"Ranking report keys: {list(ranking_report.keys())}")
        else:
            top_stocks = recommendations[:5]

            # Summary
            st.markdown("## 📊 Top 5 추천 요약")

            for rank, stock in enumerate(top_stocks, 1):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, 2, 2])

                    ticker = stock.get('ticker', 'N/A')
                    overall = stock.get('overall_score', 0)
                    tech = stock.get('technical_score', 0)

                    with col1:
                        st.metric("순위", f"#{rank}")

                    with col2:
                        st.markdown(f"**{ticker}**")
                        st.metric("종합", f"{overall:.1f}/100")
                        st.metric("기술", f"{tech:.1f}/100")

                    with col3:
                        if ticker in news_data:
                            st.markdown("**뉴스**")
                            for i, article in enumerate(news_data[ticker][:2], 1):
                                title = article.get('title', '')[:50]
                                url = article.get('url', '')
                                if url:
                                    st.markdown(f"[{i}. {title}...]({url})")
                        else:
                            st.text("뉴스 없음")

            # Export
            st.markdown("---")
            st.markdown("## 📥 다운로드")

            col1, col2 = st.columns(2)
            with col1:
                import json
                json_str = json.dumps(results, indent=2, default=str)
                st.download_button(
                    "📋 JSON",
                    json_str,
                    f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )

            with col2:
                report = "# Top 5 Recommendations\n\n"
                for rank, stock in enumerate(top_stocks, 1):
                    ticker = stock.get('ticker')
                    score = stock.get('overall_score', 0)
                    report += f"{rank}. **{ticker}**: {score:.1f}/100\n"

                st.download_button(
                    "📄 텍스트",
                    report,
                    f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain"
                )

else:
    st.info("""
    ### 👋 시작하기

    좌측에서 분석 기간을 선택하고 🚀 **분석 시작**을 누르세요.

    **기능:**
    - 6개 기술 지표 분석
    - 실시간 뉴스 통합
    - 자동 리포트 생성

    **처음 사용하시나요?**
    분석은 3-10분 정도 소요됩니다. 좌측의 기간을 선택하고 분석 시작 버튼을 누르세요.
    """)

st.markdown("---")
st.caption("⚠️ 정보 제공용, 투자 조언 아님")
