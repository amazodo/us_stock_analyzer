"""Global configuration and settings for US Stock AI Analyzer."""

import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env (local development)
load_dotenv()

# ============================================
# PROJECT PATHS
# ============================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
TICKER_DIR = DATA_DIR / "tickers"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for directory in [CACHE_DIR, TICKER_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================
# API CONFIGURATION
# ============================================

# Try to get API keys from multiple sources:
# 1. Streamlit secrets (for Streamlit Cloud)
# 2. Environment variables (for local development)
# 3. Default to empty string

def _get_secret(key_name: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variables."""
    try:
        # Try Streamlit secrets first (for Streamlit Cloud)
        import streamlit as st
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except (ImportError, AttributeError):
        pass

    # Fall back to environment variables
    return os.getenv(key_name, default)

# API Keys
# Note: Only NEWS_API_KEY is required for news integration
# ANTHROPIC_API_KEY is no longer used (sentiment analysis removed)
NEWS_API_KEY = _get_secret("NEWS_API_KEY")
TAVILY_API_KEY = _get_secret("TAVILY_API_KEY", "")

# Validate API keys (warnings only, don't crash)
if not NEWS_API_KEY:
    print("[WARNING] NEWS_API_KEY not set (optional, set in .env or Streamlit Secrets for news)")

# ============================================
# ANALYSIS SETTINGS
# ============================================

# 분석 기간 (일 단위)
ANALYSIS_PERIOD_DAYS = int(os.getenv("ANALYSIS_PERIOD_DAYS", "30"))

# 추천 종목 개수
TOP_N_RECOMMENDATIONS = int(os.getenv("TOP_N_RECOMMENDATIONS", "5"))

# 목표 상승률 (%)
TARGET_GAIN_PERCENT = float(os.getenv("TARGET_GAIN_PERCENT", "5.0"))

# ============================================
# CACHE SETTINGS
# ============================================

# 캐시 유효 기간 (시간)
CACHE_EXPIRY_HOURS = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))

# 로컬 캐싱 활성화 여부
ENABLE_LOCAL_CACHE = os.getenv("ENABLE_LOCAL_CACHE", "true").lower() == "true"

# ============================================
# LOGGING
# ============================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = PROJECT_ROOT / os.getenv("LOG_FILE", "logs/analysis.log")

# ============================================
# TECHNICAL INDICATORS WEIGHTS
# ============================================

# 기술적 지표 가중치 (합계 100)
TECHNICAL_WEIGHTS: Dict[str, float] = {
    "moving_averages": float(os.getenv("WEIGHT_MOVING_AVERAGES", "24")),
    "momentum": float(os.getenv("WEIGHT_MOMENTUM", "16")),
    "volatility": float(os.getenv("WEIGHT_VOLATILITY", "16")),
    "volume_flow": float(os.getenv("WEIGHT_VOLUME_FLOW", "16")),
    "fibonacci": float(os.getenv("WEIGHT_FIBONACCI", "8")),
    "ichimoku": float(os.getenv("WEIGHT_ICHIMOKU", "20")),
}

# Validate weights sum to 100
TOTAL_TECHNICAL_WEIGHT = sum(TECHNICAL_WEIGHTS.values())
if abs(TOTAL_TECHNICAL_WEIGHT - 100) > 0.01:
    print(f"[WARNING] Technical indicator weights sum to {TOTAL_TECHNICAL_WEIGHT}, not 100")

# 기술적 지표와 감성 분석의 최종 앙상블 가중치
ENSEMBLE_WEIGHTS = {
    "technical": 0.60,  # 60% (=quant, 기술적 지표)
    "sentiment": 0.40,  # 40% (=qual, 감성 분석)
}

# ============================================
# QUALITATIVE (SENTIMENT) WEIGHTS — NEW
# ============================================

# 감성 점수 분할 가중치 (합계 100)
QUAL_WEIGHTS: Dict[str, float] = {
    "macro": float(os.getenv("WEIGHT_QUAL_MACRO", "30")),      # 거시경제 뉴스
    "ticker": float(os.getenv("WEIGHT_QUAL_TICKER", "40")),    # 종목별 뉴스
    "expert": float(os.getenv("WEIGHT_QUAL_EXPERT", "30")),    # 전문가 의견 (Claude)
}

# Validate weights sum to 100
TOTAL_QUAL_WEIGHT = sum(QUAL_WEIGHTS.values())
if abs(TOTAL_QUAL_WEIGHT - 100) > 0.01:
    print(f"[WARNING] Qual weights sum to {TOTAL_QUAL_WEIGHT}, not 100")

# ============================================
# TECHNICAL INDICATOR SETTINGS
# ============================================

# Moving Averages
MOVING_AVERAGE_PERIODS = [20, 50, 200]
EMA_PERIODS = [12, 26]

# Momentum
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

STOCHASTIC_K_PERIOD = 14
STOCHASTIC_D_PERIOD = 3

# Volatility
BOLLINGER_PERIOD = 20
BOLLINGER_STD_DEV = 2
ATR_PERIOD = 14

# Volume
OBV_PERIOD = 20

# Fibonacci
FIBONACCI_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]

# ============================================
# SENTIMENT ANALYSIS
# ============================================

# 감성 분석 방법 (vader, llm, ensemble)
SENTIMENT_METHOD = os.getenv("SENTIMENT_METHOD", "ensemble")

# VADER 임계값
SENTIMENT_POSITIVE_THRESHOLD = float(os.getenv("SENTIMENT_POSITIVE_THRESHOLD", "0.05"))
SENTIMENT_NEGATIVE_THRESHOLD = float(os.getenv("SENTIMENT_NEGATIVE_THRESHOLD", "-0.05"))

# Claude 모델
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-1")

# ============================================
# ATR / VOLATILITY HARD FILTER  — NEW
# ============================================

# ATR 변동성 필터 임계값 (%)
# 1주일 내 5% 상승 가능성이 물리적으로 있는지 사전 검증
ATR_FEASIBILITY_THRESHOLD_PCT = float(os.getenv("ATR_FEASIBILITY_THRESHOLD_PCT", "2.5"))

# ============================================
# EARNINGS RISK  — NEW
# ============================================

# 실적 발표 리스크 윈도우 (일수)
EARNINGS_RISK_WINDOW_DAYS = int(os.getenv("EARNINGS_RISK_WINDOW_DAYS", "7"))

# 실적 발표 7일 이내 종목 감점 (포인트)
EARNINGS_RISK_PENALTY_POINTS = float(os.getenv("EARNINGS_RISK_PENALTY_POINTS", "5.0"))

# ============================================
# SECTOR MOMENTUM BONUS  — NEW
# ============================================

# 섹터 모멘텀 가산점 상한 (포인트)
SECTOR_MOMENTUM_MAX_BONUS = float(os.getenv("SECTOR_MOMENTUM_MAX_BONUS", "5.0"))

# 섹터 모멘텀 계산용 룩백 기간 (일수)
SECTOR_MOMENTUM_LOOKBACK_DAYS = int(os.getenv("SECTOR_MOMENTUM_LOOKBACK_DAYS", "20"))

# 섹터 상대 강도 비교 벤치마크 티커
SECTOR_BENCHMARK_TICKER = os.getenv("SECTOR_BENCHMARK_TICKER", "SPY")

# ============================================
# EXPERT OPINION (Claude-based)  — NEW
# ============================================

# 전문가 의견(Claude 분석) 활성화
EXPERT_OPINION_ENABLED = os.getenv("EXPERT_OPINION_ENABLED", "true").lower() == "true"

# 전문가 의견 분석 실패 시 중립값
EXPERT_OPINION_NEUTRAL_FALLBACK = 50.0

# ============================================
# MARKET REGIME BADGE  — NEW
# ============================================

# 시장 레짐 판단용 이동평균 기간 (일수)
MARKET_REGIME_MA_PERIOD = int(os.getenv("MARKET_REGIME_MA_PERIOD", "20"))

# VIX 티커
VIX_TICKER = os.getenv("VIX_TICKER", "^VIX")

# VIX 경계 수준 (이상)
VIX_CAUTION_LEVEL = float(os.getenv("VIX_CAUTION_LEVEL", "20"))

# VIX 위험 수준 (이상)
VIX_RISK_OFF_LEVEL = float(os.getenv("VIX_RISK_OFF_LEVEL", "30"))

# ============================================
# UI DEFAULTS (History Period)  — NEW
# ============================================

# Streamlit UI: 기본 분석 기간 (개월)
HISTORY_MONTHS_DEFAULT = int(os.getenv("HISTORY_MONTHS_DEFAULT", "12"))

# 최소 분석 기간 (개월)
HISTORY_MONTHS_MIN = 1

# 최대 분석 기간 (개월)
HISTORY_MONTHS_MAX = 240

# ============================================
# PDF EXPORT  — NEW
# ============================================

# PDF 내보내기 활성화
PDF_ENABLED = os.getenv("PDF_ENABLED", "true").lower() == "true"

# ============================================
# STOCK SELECTION
# ============================================

# 분석 대상 종목군 (sp100, nasdaq100, all)
TICKER_SOURCE = os.getenv("TICKER_SOURCE", "sp100")

# 최소 시가총액 (십억 달러)
MIN_MARKET_CAP = float(os.getenv("MIN_MARKET_CAP", "10"))

# 최소 일일 거래량 (만 주)
MIN_DAILY_VOLUME = float(os.getenv("MIN_DAILY_VOLUME", "1000"))

# ============================================
# OUTPUT SETTINGS
# ============================================

# 리포트 형식 (markdown, pdf, both)
REPORT_FORMAT = os.getenv("REPORT_FORMAT", "markdown")

# ============================================
# SCHEDULE
# ============================================

# 자동 분석 주기 (cron 형식)
SCHEDULE_CRON = os.getenv("SCHEDULE_CRON", "0 17 * * 5")

# ============================================
# ADVANCED OPTIONS
# ============================================

# 디버그 모드
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# 병렬 처리 활성화
ENABLE_PARALLEL = os.getenv("ENABLE_PARALLEL", "true").lower() == "true"

# 최대 병렬 작업 수
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# 재시도 횟수
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# 재시도 대기 시간 (초)
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))

# ============================================
# DEFAULT TICKERS (S&P 100)
# ============================================

DEFAULT_TICKERS: List[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "JPM", "JNJ",
    "V", "WMT", "PG", "MA", "UNH", "HD", "MCD", "INTC", "PYPL", "CRM",
    "AB", "ACN", "ADBE", "AMD", "AXP", "BA", "BAC", "BDX", "BIIB", "BMY",
    "CAT", "CMCSA", "COF", "COP", "COST", "CSCO", "CVX", "DASH", "DIS", "DUK",
    "EBAY", "EQR", "F", "FDX", "FITB", "GILD", "GM", "GOOG", "GS", "HLT",
    "HON", "IBM", "ICE", "IRM", "ISRG", "ITW", "JCI", "KO", "LLY", "LOW",
    "LVS", "LYV", "MMC", "MO", "MNST", "MU", "NBL", "NEE", "NKE", "NOW",
    "NTAP", "ORCL", "PCAR", "PEP", "PFE", "PGR", "PM", "POWER", "PRU", "PSA",
    "PYPL", "QCOM", "REGN", "ROST", "RTX", "SBUX", "SCHW", "SO", "SPG", "SPOT",
]

# ============================================
# HELPER FUNCTIONS
# ============================================


def get_config_summary() -> str:
    """Return a summary of current configuration."""
    return f"""
    Configuration Summary
    =====================
    Project Root: {PROJECT_ROOT}
    Analysis Period: {ANALYSIS_PERIOD_DAYS} days
    Top N Recommendations: {TOP_N_RECOMMENDATIONS}
    Target Gain: {TARGET_GAIN_PERCENT}%

    Technical Weights: {TECHNICAL_WEIGHTS}
    Qualitative Weights: {QUAL_WEIGHTS}
    Ensemble Weights: {ENSEMBLE_WEIGHTS}
    Sentiment Method: {SENTIMENT_METHOD}

    ATR Threshold: {ATR_FEASIBILITY_THRESHOLD_PCT}%
    Earnings Risk Window: {EARNINGS_RISK_WINDOW_DAYS} days
    Sector Momentum Max: {SECTOR_MOMENTUM_MAX_BONUS} points
    Expert Opinion Enabled: {EXPERT_OPINION_ENABLED}

    Cache Enabled: {ENABLE_LOCAL_CACHE}
    Cache Expiry: {CACHE_EXPIRY_HOURS} hours

    PDF Export: {PDF_ENABLED}
    UI History Default: {HISTORY_MONTHS_DEFAULT} months

    Debug Mode: {DEBUG}
    Parallel Processing: {ENABLE_PARALLEL} (Max Workers: {MAX_WORKERS})
    """


if __name__ == "__main__":
    print(get_config_summary())
