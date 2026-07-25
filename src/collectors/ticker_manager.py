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

    def __init__(self):
        self.sp100 = []
        self.nasdaq100 = []
        self.unified_universe = []
        self._load_tickers()

    def _load_tickers(self):
        """Load tickers from JSON file."""
        try:
            ticker_file = TICKER_DIR / "sp100_nasdaq100.json"

            if not ticker_file.exists():
                logger.warning(f"Ticker file not found: {ticker_file}")
                self.sp100 = []
                self.nasdaq100 = []
            else:
                with open(ticker_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.sp100 = data.get('sp100', [])
                self.nasdaq100 = data.get('nasdaq100', [])

                logger.info(f"OK Loaded {len(self.sp100)} S&P 100 tickers")
                logger.info(f"OK Loaded {len(self.nasdaq100)} NASDAQ 100 tickers")

            # Create unified universe (remove duplicates and blacklisted)
            all_tickers = set(self.sp100 + self.nasdaq100)
            self.unified_universe = [t for t in sorted(all_tickers) if t not in self.BLACKLIST]

            excluded_count = len(all_tickers) - len(self.unified_universe)
            logger.info(f"OK Unified universe: {len(self.unified_universe)} tickers ({excluded_count} delisted/excluded)")

        except Exception as e:
            logger.error(f"Error loading tickers: {e}")
            self.sp100 = []
            self.nasdaq100 = []
            self.unified_universe = []

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

