"""Stock data collection using yfinance."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import yfinance as yf

from config.settings import ANALYSIS_PERIOD_DAYS, CACHE_DIR, ENABLE_LOCAL_CACHE, EARNINGS_RISK_WINDOW_DAYS

logger = logging.getLogger(__name__)


class StockDataCollector:
    """Collects stock price and volume data from yfinance."""

    def __init__(self, use_cache: bool = ENABLE_LOCAL_CACHE):
        self.use_cache = use_cache
        self.cache_dir = CACHE_DIR / "stock_data"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_historical_data(
        self,
        ticker: str,
        period_days: int = ANALYSIS_PERIOD_DAYS,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data for a stock.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            period_days: Number of days of historical data to fetch

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Adj Close
        """
        try:
            logger.debug(f"Fetching historical data for {ticker} ({period_days} days)")

            # Fetch data
            stock = yf.Ticker(ticker)
            df = stock.history(period=f"{period_days}d")

            if df.empty:
                logger.warning(f"No data found for ticker: {ticker}")
                return None

            logger.info(f"PASS Fetched {len(df)} rows for {ticker}")
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """
        Fetch stock information (market cap, sector, industry, etc).

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with stock info or None if error
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                'ticker': ticker,
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'beta': info.get('beta', 0),
            }

        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return None

    def get_intraday_data(
        self,
        ticker: str,
        interval: str = "1h"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch intraday data for real-time analysis.

        Args:
            ticker: Stock ticker symbol
            interval: Time interval ('1m', '5m', '15m', '1h', '1d')

        Returns:
            DataFrame with intraday OHLCV data
        """
        try:
            logger.debug(f"Fetching {interval} intraday data for {ticker}")

            stock = yf.Ticker(ticker)
            df = stock.history(interval=interval, period="1d")

            if df.empty:
                logger.warning(f"No intraday data for {ticker}")
                return None

            logger.info(f"OK Fetched intraday data for {ticker} ({interval})")
            return df

        except Exception as e:
            logger.error(f"Error fetching intraday data for {ticker}: {e}")
            return None

    def get_batch_data(self, tickers: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple tickers efficiently.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary {ticker: DataFrame}
        """
        data = {}
        for ticker in tickers:
            df = self.get_historical_data(ticker)
            if df is not None:
                data[ticker] = df

        logger.info(f"OK Fetched data for {len(data)}/{len(tickers)} tickers")
        return data

    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate daily and cumulative returns.

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with additional return columns
        """
        df = df.copy()
        df['Daily_Return'] = df['Adj Close'].pct_change()
        df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1

        return df

    def calculate_volatility(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        Calculate rolling volatility.

        Args:
            df: OHLCV DataFrame
            window: Rolling window size

        Returns:
            DataFrame with volatility column
        """
        df = df.copy()
        if 'Daily_Return' not in df.columns:
            df['Daily_Return'] = df['Adj Close'].pct_change()

        df['Volatility'] = df['Daily_Return'].rolling(window=window).std()
        return df

    def get_earnings_risk(
        self,
        ticker: str,
        window_days: int = EARNINGS_RISK_WINDOW_DAYS
    ) -> Dict:
        """
        Check if stock has earnings call/announcement within the next N days.

        Args:
            ticker: Stock ticker symbol
            window_days: Risk window in days (default 7)

        Returns:
            Dictionary with:
              - 'next_earnings_date': ISO format date string or None
              - 'days_until': int or None
              - 'within_risk_window': bool (True if earnings within window_days)
        """
        try:
            stock = yf.Ticker(ticker)

            # Try to get earnings dates via get_earnings_dates() method
            try:
                earnings_dates = stock.get_earnings_dates(limit=5)
                if earnings_dates is not None and len(earnings_dates) > 0:
                    # earnings_dates is a DataFrame with earnings dates
                    # Get the nearest future earnings date
                    today = pd.Timestamp.now().normalize()
                    future_earnings = earnings_dates[earnings_dates.index > today]

                    if len(future_earnings) > 0:
                        nearest_earnings = future_earnings.index[0]
                        days_until = (nearest_earnings - today).days

                        return {
                            'next_earnings_date': nearest_earnings.isoformat(),
                            'days_until': days_until,
                            'within_risk_window': days_until <= window_days
                        }
            except (AttributeError, TypeError, Exception):
                # Method may not exist or may fail for some tickers
                pass

            # Fallback: check .calendar attribute
            try:
                calendar = stock.calendar
                if calendar is not None and not calendar.empty:
                    earnings_date = calendar['Earnings Date'].iloc[0]
                    if pd.notna(earnings_date):
                        today = pd.Timestamp.now().normalize()
                        earnings_ts = pd.Timestamp(earnings_date).normalize()
                        days_until = (earnings_ts - today).days

                        return {
                            'next_earnings_date': earnings_ts.isoformat(),
                            'days_until': days_until,
                            'within_risk_window': 0 <= days_until <= window_days
                        }
            except (AttributeError, TypeError, Exception):
                pass

            # No earnings data found or unable to parse
            return {
                'next_earnings_date': None,
                'days_until': None,
                'within_risk_window': False
            }

        except Exception as e:
            logger.debug(f"Error fetching earnings risk for {ticker}: {e}")
            return {
                'next_earnings_date': None,
                'days_until': None,
                'within_risk_window': False
            }


# Convenience functions
def fetch_stock_data(ticker: str) -> Optional[pd.DataFrame]:
    """Quick function to fetch stock data."""
    collector = StockDataCollector()
    return collector.get_historical_data(ticker)


def fetch_batch_data(tickers: List[str]) -> Dict[str, pd.DataFrame]:
    """Quick function to fetch data for multiple tickers."""
    collector = StockDataCollector()
    return collector.get_batch_data(tickers)

