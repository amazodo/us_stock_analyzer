"""Manage S&P 100 and NASDAQ 100 ticker lists."""

import json
import logging
from typing import List, Set
from pathlib import Path

from config.settings import TICKER_DIR

logger = logging.getLogger(__name__)


class TickerManager:
    """Load and manage ticker universes."""

    # Known delisted/problem tickers (no data available)
    BLACKLIST = {
        'ATVI', 'ANSS', 'BRK.B', 'CCXI', 'CMF', 'MMC', 'NBL', 'PLYA',
        'SPLK', 'SQ', 'TESLA', 'TWILIO', 'ZSCALER'
    }

    # Default ticker lists (S&P 100 + NASDAQ 100)
    DEFAULT_SP100 = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AVGO',
        'NFLX', 'ASML', 'COST', 'JPM', 'JNPR', 'KO', 'MCD', 'NKE',
        'PG', 'V', 'WMT', 'XOM', 'CVX', 'JNJ', 'LLY', 'UNH',
        'MA', 'PYPL', 'ADBE', 'CRM', 'NFLX', 'INTC', 'AMD', 'QCOM',
        'MU', 'CSCO', 'ORCL', 'IBM', 'ACN', 'AMAT', 'CDNS', 'ADSK',
        'FAST', 'FTNT', 'MCHP', 'NVDA', 'GOOGL', 'BDX', 'ABT', 'CAT',
        'DE', 'GE', 'HON', 'BA', 'RTX', 'LMT', 'GD', 'NOC'
    ]

    DEFAULT_NASDAQ100 = [
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'TSLA', 'META',
        'AVGO', 'NFLX', 'ASML', 'COST', 'AMAZON', 'BROADCOM', 'NETFLIX',
        'ADOBE', 'INTC', 'AMD', 'QCOM', 'MU', 'LRCX', 'MARVELL', 'AMAT',
        'CDNS', 'SNPS', 'ADSK', 'ANSS', 'ABNB', 'AIRB', 'DASH', 'DDOG',
        'ESTC', 'NTNX', 'OKTA', 'PSTG', 'SNOW', 'CRWD', 'CRM', 'PAYC',
        'ADBE', 'COIN', 'MSTR', 'RIOT', 'MARA', 'CLSK', 'WDAY', 'VEEV',
        'SPLK', 'OKTA', 'ZM', 'FTNT', 'PANW', 'PALO', 'SENTIO', 'CHECKPOINT'
    ]

    def __init__(self):
        self.sp100 = []
        self.nasdaq100 = []
        self.unified_universe = []
        self._load_tickers()

    def _load_tickers(self):
        """Load tickers from JSON file or use defaults."""
        try:
            ticker_file = TICKER_DIR / "sp100_nasdaq100.json"

            if ticker_file.exists():
                with open(ticker_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.sp100 = data.get('sp100', self.DEFAULT_SP100)
                self.nasdaq100 = data.get('nasdaq100', self.DEFAULT_NASDAQ100)
                logger.info(f"✅ Loaded {len(self.sp100)} S&P 100 tickers from file")
                logger.info(f"✅ Loaded {len(self.nasdaq100)} NASDAQ 100 tickers from file")
            else:
                # Use default tickers if file doesn't exist
                self.sp100 = self.DEFAULT_SP100
                self.nasdaq100 = self.DEFAULT_NASDAQ100
                logger.info(f"⚠️ Using default {len(self.sp100)} S&P 100 tickers (file not found)")
                logger.info(f"⚠️ Using default {len(self.nasdaq100)} NASDAQ 100 tickers (file not found)")

            # Create unified universe (remove duplicates and blacklisted)
            all_tickers = set(self.sp100 + self.nasdaq100)
            self.unified_universe = [t for t in sorted(all_tickers) if t not in self.BLACKLIST]

            excluded_count = len(all_tickers) - len(self.unified_universe)
            logger.info(f"✅ Unified universe: {len(self.unified_universe)} tickers ({excluded_count} delisted/excluded)")

        except Exception as e:
            logger.error(f"Error loading tickers: {e}")
            # Fall back to defaults
            self.sp100 = self.DEFAULT_SP100
            self.nasdaq100 = self.DEFAULT_NASDAQ100
            all_tickers = set(self.sp100 + self.nasdaq100)
            self.unified_universe = [t for t in sorted(all_tickers) if t not in self.BLACKLIST]
            logger.info(f"⚠️ Fallback to defaults: {len(self.unified_universe)} tickers")

    def get_sp100(self) -> List[str]:
        """Get S&P 100 tickers (excluding blacklisted)."""
        return [t for t in self.sp100 if t not in self.BLACKLIST]

    def get_nasdaq100(self) -> List[str]:
        """Get NASDAQ 100 tickers (excluding blacklisted)."""
        return [t for t in self.nasdaq100 if t not in self.BLACKLIST]

    def get_unified_universe(self) -> List[str]:
        """Get unified S&P 100 + NASDAQ 100 (deduplicated)."""
        return self.unified_universe

    def get_tickers_by_source(self, source: str = "unified") -> List[str]:
        """
        Get tickers by source.

        Args:
            source: "sp100", "nasdaq100", or "unified"

        Returns:
            List of tickers
        """
        if source == "sp100":
            return self.get_sp100()
        elif source == "nasdaq100":
            return self.get_nasdaq100()
        else:
            return self.get_unified_universe()

    def count_tickers(self) -> dict:
        """Get ticker counts."""
        return {
            'sp100': len(self.sp100),
            'nasdaq100': len(self.nasdaq100),
            'unified': len(self.unified_universe),
        }

    def validate_ticker(self, ticker: str) -> bool:
        """Check if ticker is in universe."""
        return ticker in self.unified_universe


# Global instance
_ticker_manager = None


def get_ticker_manager() -> TickerManager:
    """Get global ticker manager instance."""
    global _ticker_manager
    if _ticker_manager is None:
        _ticker_manager = TickerManager()
    return _ticker_manager


def get_analysis_tickers(source: str = "unified") -> List[str]:
    """Quick function to get tickers for analysis."""
    manager = get_ticker_manager()
    return manager.get_tickers_by_source(source)

