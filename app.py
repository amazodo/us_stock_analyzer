"""Streamlit app - US Stock AI Analyzer."""

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

# Setup
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="US Stock AI Analyzer",
    page_icon="📈",
    layout="wide",
)

st.markdown("# 📊 US Stock AI Analyzer")
st.markdown("**기술적 지표 기반 Top 5 종목 추천 시스템** (실시간 뉴스 통합)")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ 분석 설정")
    
    period_options = [
        ("1개월", 30),
        ("3개월", 90),
        ("6개월", 180),
        ("1년", 365),
    ]
    selected_period = st.selectbox("분석 기간", period_options, index=3)
    period_days = selected_period[1]
    
    st.markdown("---")
    st.markdown("### 📊 기술 지표 (6개)")
    st.info("이동평균 (24%) • 모멘텀 (16%) • 변동성 (16%) • 거래량 (16%) • 피보나치 (8%) • 일목균형표 (20%)")
    
    st.markdown("---")
    run_analysis = st.button("🚀 분석 시작", use_container_width=True, type="primary")

# Main content
if run_analysis:
    with st.spinner("🔄 분석 중... (3-10분 소요)"):
        try:
            # Run pipeline
            logger.info(f"Starting analysis with {period_days} days")
            st.write("🔍 파이프라인 초기화 중...")

            pipeline = AnalysisPipeline(period_days=period_days)
            st.write("📊 분석 실행 중...")

            results = pipeline.run_full_analysis()
            st.write(f"✅ 분석 완료 - 결과 타입: {type(results)}")
            st.write(f"✅ 결과 키: {list(results.keys()) if results else 'None'}")
            
            # Fetch news for top 5
            logger.info("Fetching news for top 5 stocks")
            ranking_report = results.get('ranking_report', {})
            st.write(f"📋 Ranking Report 키: {list(ranking_report.keys())}")

            top_stocks = ranking_report.get('recommendations', [])[:5]
            st.write(f"📊 Top Stocks 개수: {len(top_stocks)}")

            if not top_stocks:
                st.error("❌ 추천 종목이 없습니다. 분석 결과를 확인하세요.")
                st.write(f"DEBUG - Ranking Report: {ranking_report}")
                st.stop()
            
            news_collector = NewsDataCollector()
            news_data = {}
            for stock in top_stocks:
                ticker = stock.get('ticker')
                try:
                    articles = news_collector.search_ticker_news(ticker, period_days=30)
                    if articles:
                        news_data[ticker] = articles
                except Exception as e:
                    logger.debug(f"News fetch failed for {ticker}: {e}")
            
            logger.info(f"Fetched news for {len(news_data)}/{len(top_stocks)} stocks")

            # Save to session state
            st.session_state['results'] = results
            st.session_state['news_data'] = news_data

            if len(news_data) < len(top_stocks):
                st.success(f"✅ 분석 완료! (뉴스: {len(news_data)}/{len(top_stocks)} - API 할당량 제한)")
            else:
                st.success("✅ 분석 완료!")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            st.error(f"❌ 오류: {str(e)}")

# Display results
if 'results' in st.session_state:
    results = st.session_state['results']
    news_data = st.session_state.get('news_data', {})
    
    # Summary
    render_summary_view(results)
    st.markdown("---")
    
    # Top 5 with news
    st.markdown("## 🏆 Top 5 추천 종목")
    
    ranking_report = results.get('ranking_report', {})
    top_stocks = ranking_report.get('recommendations', [])[:5]
    
    for rank, stock in enumerate(top_stocks, 1):
        col1, col2, col3 = st.columns([1, 2, 2])
        
        ticker = stock.get('ticker', 'N/A')
        overall = stock.get('overall_score', 0)
        tech = stock.get('technical_score', 0)
        
        with col1:
            st.markdown(f"### #{rank}")
        
        with col2:
            st.markdown(f"**{ticker}**")
            st.metric("종합", f"{overall:.1f}/100")
            st.metric("기술", f"{tech:.1f}/100")
        
        with col3:
            if ticker in news_data:
                articles = news_data[ticker]
                st.markdown("**최신 뉴스**")
                for i, article in enumerate(articles[:3], 1):
                    title = article.get('title', 'No title')[:60]
                    url = article.get('url', '')
                    if url:
                        st.markdown(f"{i}. [{title}...]({url})")
                    else:
                        st.text(f"{i}. {title}...")
            else:
                st.text("뉴스 정보 없음")
        
        st.markdown("---")
    
    st.markdown("---")
    
    # Detailed view
    render_detail_view(results, news_data)
    
    st.markdown("---")
    
    # Export
    st.markdown("## 📥 리포트 다운로드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_text = f"""# 📊 Top 5 Stock Recommendations

**분석 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**분석 기간**: {period_days}일
**방법론**: 기술적 지표 6개 (100%)

## 🏆 Top 5 추천 종목

"""
        for rank, stock in enumerate(top_stocks, 1):
            ticker = stock.get('ticker', 'N/A')
            overall = stock.get('overall_score', 0)
            tech = stock.get('technical_score', 0)
            
            report_text += f"### #{rank}. {ticker}\n"
            report_text += f"- 종합 점수: {overall:.1f}/100\n"
            report_text += f"- 기술 점수: {tech:.1f}/100\n"
            report_text += f"- 목표: 1주일 내 5% 상승\n\n"
            
            if ticker in news_data:
                report_text += "**최신 뉴스**:\n"
                for article in news_data[ticker][:3]:
                    title = article.get('title', 'N/A')
                    url = article.get('url', '')
                    report_text += f"- [{title}]({url})\n"
                report_text += "\n"
        
        st.download_button(
            label="📄 마크다운 다운로드",
            data=report_text,
            file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with col2:
        import json
        json_data = json.dumps(results, indent=2, default=str)
        st.download_button(
            label="📊 JSON 다운로드",
            data=json_data,
            file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

else:
    st.markdown("""
    ## 👋 시작하기
    
    왼쪽 사이드바에서 분석 기간을 선택하고 **🚀 분석 시작**을 클릭하세요.
    
    ### 📊 분석 기능
    - **6개 기술 지표**: 종합적인 기술적 분석
    - **실시간 뉴스**: Top5 종목별 최신 뉴스
    - **섹터 모멘텀**: 업종별 상대 강도
    - **실적 리스크**: 실적 발표 일정 확인
    - **자동 필터**: ATR 기반 변동성 검증
    """)

st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #999; font-size: 11px; margin-top: 2rem;'>
    <p>📈 US Stock AI Analyzer | 기술적 지표 기반 분석</p>
    <p>⚠️ 본 분석은 정보 제공용이며 투자 조언이 아닙니다</p>
    </div>
""", unsafe_allow_html=True)
