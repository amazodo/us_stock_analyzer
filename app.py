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
            pipeline = AnalysisPipeline(period_days=period_days)
            results = pipeline.run_full_analysis()
            
            if not results:
                st.error("분석 실패: 결과가 없습니다.")
                logger.error("Pipeline returned None or empty results")
                st.stop()
            
            st.session_state['results'] = results
            
            # Fetch news
            ranking_report = results.get('ranking_report', {})
            top_stocks = ranking_report.get('recommendations', [])[:5]
            
            if top_stocks:
                news_data = {}
                news_collector = NewsDataCollector()
                for stock in top_stocks:
                    ticker = stock.get('ticker')
                    try:
                        articles = news_collector.search_ticker_news(ticker, period_days=30)
                        if articles:
                            news_data[ticker] = articles
                    except:
                        pass
                st.session_state['news_data'] = news_data
            
            st.success(f"✅ 완료! ({len(top_stocks)} 종목 분석)")
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            st.error(f"❌ 오류: {str(e)}")

# Display results
if st.session_state['results']:
    results = st.session_state['results']
    news_data = st.session_state.get('news_data', {})
    
    # Summary
    st.markdown("## 📊 Top 5 추천 요약")
    ranking_report = results.get('ranking_report', {})
    top_stocks = ranking_report.get('recommendations', [])[:5]
    
    if not top_stocks:
        st.warning("추천 종목이 없습니다.")
    else:
        # Display top 5
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
                "JSON",
                json_str,
                f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json"
            )
        
        with col2:
            report = "# Top 5\n\n"
            for rank, stock in enumerate(top_stocks, 1):
                ticker = stock.get('ticker')
                score = stock.get('overall_score', 0)
                report += f"{rank}. {ticker}: {score:.1f}/100\n"
            
            st.download_button(
                "텍스트",
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
    """)

st.markdown("---")
st.caption("⚠️ 정보 제공용, 투자 조언 아님")
