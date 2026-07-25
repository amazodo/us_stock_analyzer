"""Streamlit app - US Stock AI Analyzer."""

import sys
import os

# Fix path for Streamlit Cloud
if '/mount/src' in os.getcwd():
    sys.path.insert(0, '/mount/src/us_stock_analyzer')
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime
import json
import logging

logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

from src.pipeline import AnalysisPipeline
from src.collectors.news_data import NewsDataCollector

# Page config
st.set_page_config(
    page_title="US Stock AI Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.markdown("# 📊 US Stock AI Analyzer")
st.markdown("**기술적 지표 기반 Top 5 종목 추천**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ 분석 설정")

    period_options = [("1개월", 30), ("3개월", 90), ("6개월", 180), ("1년", 365)]
    selected = st.selectbox("분석 기간", period_options, index=3)
    period_days = selected[1]

    st.markdown("---")
    st.info("**6개 기술 지표**\n\n• 이동평균\n• 모멘텀\n• 변동성\n• 거래량\n• 피보나치\n• 일목균형표")

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'news_data' not in st.session_state:
    st.session_state.news_data = {}

# Main content
if not st.session_state.analysis_complete:
    # Analysis button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🚀 분석 시작", use_container_width=True, type="primary"):
            try:
                # Progress tracking
                progress_container = st.container()
                with progress_container:
                    status = st.empty()
                    progress = st.progress(0)

                    # Step 1: Initialize
                    status.text("🔄 파이프라인 초기화 중...")
                    progress.progress(5)

                    pipeline = AnalysisPipeline(period_days=period_days)

                    # Step 2: Run analysis
                    status.text("📊 분석 실행 중... (2-5분)")
                    progress.progress(25)

                    results = pipeline.run_full_analysis()

                    progress.progress(70)

                    # Validate results
                    if not results:
                        st.error("❌ 분석 실패: 결과가 없습니다")
                        st.stop()

                    ranking_report = results.get('ranking_report', {})
                    if not ranking_report:
                        st.error("❌ 순위 데이터 없음")
                        st.stop()

                    recommendations = ranking_report.get('recommendations', [])
                    if not recommendations:
                        st.error(f"❌ 추천 없음 (분석: {results.get('tickers_analyzed', 0)})")
                        st.stop()

                    top_stocks = recommendations[:5]

                    # Step 3: Fetch news
                    status.text("📰 뉴스 수집 중...")
                    progress.progress(85)

                    news_data = {}
                    try:
                        news_collector = NewsDataCollector()
                        for stock in top_stocks:
                            ticker = stock.get('ticker')
                            try:
                                articles = news_collector.search_ticker_news(ticker, period_days=30)
                                if articles:
                                    news_data[ticker] = articles
                            except:
                                pass
                    except:
                        pass

                    # Store results
                    st.session_state.results = results
                    st.session_state.news_data = news_data
                    st.session_state.analysis_complete = True

                    progress.progress(100)
                    status.text("✅ 분석 완료!")

                    # Clear status after 2 seconds
                    import time
                    time.sleep(1)
                    progress_container.empty()

            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

# Display results if analysis is complete
if st.session_state.analysis_complete and st.session_state.results:
    results = st.session_state.results
    news_data = st.session_state.news_data

    ranking_report = results.get('ranking_report', {})
    recommendations = ranking_report.get('recommendations', [])
    top_stocks = recommendations[:5] if recommendations else []

    if top_stocks:
        # Results header
        st.markdown("## 📈 분석 결과")
        st.success(f"✅ 분석 완료! ({len(top_stocks)}개 종목, 뉴스: {len(news_data)}개)")

        # Top 5 cards
        st.markdown("### Top 5 추천 종목")

        for rank, stock in enumerate(top_stocks, 1):
            ticker = stock.get('ticker', 'N/A')
            overall = float(stock.get('overall_score', 0))
            tech = float(stock.get('technical_score', 0))

            with st.container(border=True):
                col1, col2, col3 = st.columns([0.8, 2, 2.2])

                with col1:
                    st.markdown(f"### #{rank}")

                with col2:
                    st.markdown(f"## {ticker}")
                    st.metric("종합", f"{overall:.1f}/100")

                with col3:
                    st.metric("기술", f"{tech:.1f}/100")

                    if ticker in news_data:
                        st.markdown("**최신 뉴스:**")
                        for i, article in enumerate(news_data[ticker][:2], 1):
                            title = article.get('title', '')
                            url = article.get('url', '')
                            if url and title:
                                short_title = (title[:50] + '...') if len(title) > 50 else title
                                st.markdown(f"[{i}. {short_title}]({url})")

        # Statistics
        with st.expander("📊 분석 통계"):
            dist = ranking_report.get('score_distribution', {})

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("평균 점수", f"{dist.get('mean', 0):.1f}/100")
            with col2:
                st.metric("최고 점수", f"{dist.get('max', 0):.1f}/100")
            with col3:
                st.metric("최저 점수", f"{dist.get('min', 0):.1f}/100")
            with col4:
                st.metric("분석 종목", f"{len(recommendations)}")

        # Export section
        st.markdown("---")
        st.markdown("### 📥 데이터 다운로드")

        col1, col2 = st.columns(2)

        with col1:
            # JSON export
            json_data = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="📋 JSON 데이터",
                data=json_data,
                file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

        with col2:
            # Text report export
            report = "# Top 5 Recommendations\n\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            for rank, stock in enumerate(top_stocks, 1):
                ticker = stock.get('ticker')
                overall = stock.get('overall_score', 0)
                tech = stock.get('technical_score', 0)

                report += f"## {rank}. {ticker}\n"
                report += f"- Overall Score: {overall:.1f}/100\n"
                report += f"- Technical Score: {tech:.1f}/100\n"

                if ticker in news_data:
                    report += f"- Latest News:\n"
                    for i, article in enumerate(news_data[ticker][:2], 1):
                        title = article.get('title', '')
                        url = article.get('url', '')
                        if url:
                            report += f"  {i}. [{title}]({url})\n"

                report += "\n"

            st.download_button(
                label="📄 텍스트 리포트",
                data=report,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

        # Reset button
        st.markdown("---")
        if st.button("🔄 새 분석 시작"):
            st.session_state.analysis_complete = False
            st.session_state.results = None
            st.session_state.news_data = {}
            st.rerun()

    else:
        st.error("❌ 추천 종목이 없습니다. 다시 시도하세요.")

else:
    # Welcome screen
    if not st.session_state.analysis_complete:
        st.info("""
        ### 👋 US Stock AI Analyzer에 오신 것을 환영합니다!

        **사용 방법:**
        1. 좌측 사이드바에서 분석 기간을 선택하세요 (기본값: 1년)
        2. **🚀 분석 시작** 버튼을 클릭하세요
        3. 분석 완료 후 Top 5 추천 종목을 확인하세요

        **분석 내용:**
        - ✅ 6개 기술 지표 앙상블 분석
        - ✅ 실시간 뉴스 통합
        - ✅ 자동 리포트 생성
        - ✅ JSON & 텍스트 다운로드

        **소요 시간:** 첫 실행은 3-10분, 재분석은 2-5분
        """)

st.markdown("---")
st.caption("⚠️ 정보 제공용이며 투자 조언이 아닙니다.")
