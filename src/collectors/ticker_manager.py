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
        'SQ', 'TSLA_OLD', 'TWILIO', 'ZSCALER'
    }

    # Default ticker list - Top 100+ US stocks (S&P 100 + select NASDAQ 100)
    # Carefully curated to avoid duplicates and delisted tickers
    DEFAULT_TICKERS = [
        # Mega-cap tech (8)
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'AVGO', 'GOOG',
        # Consumer tech (7)
        'NFLX', 'ASML', 'INTC', 'AMD', 'QCOM', 'MU', 'AMAT',
        # Semiconductors (6)
        'CDNS', 'SNPS', 'MCHP', 'MARVELL', 'KLAC', 'LSCC',
        # Software & Cloud (8)
        'ORCL', 'CRM', 'ADBE', 'WDAY', 'SNOW', 'OKTA', 'CRWD', 'PSTG',
        # Design & analytics (4)
        'ADSK', 'BKNG', 'VRSK', 'BLDR',
        # E-commerce & payment (6)
        'PYPL', 'MA', 'V', 'DIS', 'ABNB', 'COIN',
        # Transportation (3)
        'TSLA', 'UBER', 'LYFT',
        # Retail & consumer (9)
        'WMT', 'COST', 'MCD', 'NKE', 'KO', 'PG', 'JNJ', 'PEP', 'LRCX',
        # Telecom & Media (5)
        'T', 'VZ', 'CMCSA', 'PARA', 'FOXA',
        # Energy (5)
        'XOM', 'CVX', 'COP', 'EOG', 'MPC',
        # Financial services (7)
        'JPM', 'BAC', 'GS', 'MS', 'BLK', 'SCHW', 'CME',
        # Healthcare & Pharma (9)
        'LLY', 'UNH', 'ABT', 'BDX', 'ISRG', 'ZTS', 'SYK', 'ILMN', 'REGN',
        # Industrial & Defense (8)
        'CAT', 'DE', 'HON', 'BA', 'RTX', 'LMT', 'GD', 'NOC',
        # Materials (3)
        'NEM', 'SCCO', 'FCX',
        # Utilities (4)
        'NEE', 'DUK', 'SO', 'EXC',
        # Real estate (4)
        'PLD', 'PSA', 'SPG', 'AVB',
        # Cloud & Data (6)
        'DASH', 'DDOG', 'ZM', 'SNAP', 'PINS', 'TTD',
        # Diversified (6)
        'GE', 'MMM', 'ACN', 'BRK.A', 'PM', 'AXP',
        # Crypto & growth (4)
        'MSTR', 'RIOT', 'COIN', 'ETN',
        # Additional quality stocks (5)
        'KHC', 'CIB', 'VEEV', 'CHWY', 'UPST'
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
                # Support both old format and new format
                if 'tickers' in data:
                    all_tickers = data.get('tickers', self.DEFAULT_TICKERS)
                else:
                    # Old format with sp100 and nasdaq100 separately
                    sp100 = data.get('sp100', [])
                    nasdaq100 = data.get('nasdaq100', [])
                    all_tickers = list(set(sp100 + nasdaq100))

                self.sp100 = data.get('sp100', self.DEFAULT_TICKERS[:50])
                self.nasdaq100 = data.get('nasdaq100', self.DEFAULT_TICKERS[50:])
                logger.info(f"✅ Loaded {len(all_tickers)} tickers from file")
            else:
                # Use default tickers if file doesn't exist
                all_tickers = self.DEFAULT_TICKERS
                self.sp100 = self.DEFAULT_TICKERS[:50]
                self.nasdaq100 = self.DEFAULT_TICKERS[50:]
                logger.info(f"⚠️ Using default {len(all_tickers)} tickers (file not found)")

            # Create unified universe (remove duplicates and blacklisted)
            all_tickers_set = set(all_tickers)
            self.unified_universe = [t for t in sorted(all_tickers_set) if t not in self.BLACKLIST]

            excluded_count = len(all_tickers_set) - len(self.unified_universe)
            logger.info(f"✅ Universe: {len(self.unified_universe)} tickers ({excluded_count} excluded)")

        except Exception as e:
            logger.error(f"Error loading tickers: {e}")
            # Fall back to defaults
            all_tickers = set(self.DEFAULT_TICKERS)
            self.unified_universe = [t for t in sorted(all_tickers) if t not in self.BLACKLIST]
            logger.info(f"⚠️ Fallback to defaults: {len(self.unified_universe)} tickers")

    def get_sp100(self) -> List[str]:
        """Get S&P 100 tickers (excluding blacklisted)."""
        return [t for t in self.sp100 if t not in self.BLACKLIST and t in self.unified_universe]

    def get_nasdaq100(self) -> List[str]:
        """Get NASDAQ 100 tickers (excluding blacklisted)."""
        return [t for t in self.nasdaq100 if t not in self.BLACKLIST and t in self.unified_universe]

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

