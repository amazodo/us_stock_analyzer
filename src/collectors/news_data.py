"""News data collection from NewsAPI and web search."""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

from config.settings import NEWS_API_KEY, ANALYSIS_PERIOD_DAYS, CACHE_DIR

logger = logging.getLogger(__name__)


class NewsDataCollector:
    """Collects news articles from NewsAPI."""

    def __init__(self, api_key: str = NEWS_API_KEY):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.cache_dir = CACHE_DIR / "news_data"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def search_news(
        self,
        query: str,
        period_days: int = ANALYSIS_PERIOD_DAYS,
        language: str = "en",
        sort_by: str = "relevancy"
    ) -> Optional[List[Dict]]:
        """
        Search for news articles using NewsAPI.

        Args:
            query: Search query (e.g., 'AAPL Apple earnings')
            period_days: Number of days back to search
            language: Language code (en, es, fr, etc.)
            sort_by: Sort order (relevancy, popularity, publishedAt)

        Returns:
            List of news articles or None if error
        """
        if not self.api_key:
            logger.error("NEWS_API_KEY not configured")
            return None

        try:
            # Calculate date range
            from_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')

            params = {
                'q': query,
                'from': from_date,
                'to': to_date,
                'language': language,
                'sortBy': sort_by,
                'apiKey': self.api_key,
                'pageSize': 100,  # Max results per request
            }

            logger.debug(f"Searching news for: {query}")

            # Rate limiting: NewsAPI free plan allows ~100 requests/day
            # Add delay to avoid 429 errors (conservative: 1 request per 1.5 seconds)
            time.sleep(1.5)

            response = requests.get(f"{self.base_url}/everything", params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') != 'ok':
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return None

            articles = data.get('articles', [])
            logger.info(f"OK Found {len(articles)} articles for '{query}'")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news for '{query}': {e}")
            return None

    def search_ticker_news(self, ticker: str, period_days: int = ANALYSIS_PERIOD_DAYS) -> Optional[List[Dict]]:
        """
        Search for news about a specific stock ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            period_days: Number of days back to search

        Returns:
            List of news articles
        """
        query = f"{ticker} stock"
        return self.search_news(query, period_days=period_days)

    def search_macro_news(self, period_days: int = ANALYSIS_PERIOD_DAYS) -> Optional[List[Dict]]:
        """
        Search for macroeconomic news (Fed, inflation, employment, etc.).

        Args:
            period_days: Number of days back to search

        Returns:
            List of macro news articles
        """
        macro_queries = [
            "Federal Reserve interest rates",
            "inflation economy",
            "employment jobs report",
            "stock market outlook",
            "economic recession",
        ]

        all_articles = []
        for query in macro_queries:
            articles = self.search_news(query, period_days=period_days)
            if articles:
                all_articles.extend(articles)

        logger.info(f"OK Fetched {len(all_articles)} macro news articles")
        return all_articles

    def search_batch_news(self, tickers: List[str], period_days: int = ANALYSIS_PERIOD_DAYS) -> Dict[str, List[Dict]]:
        """
        Fetch news for multiple tickers.

        Args:
            tickers: List of ticker symbols
            period_days: Number of days back to search

        Returns:
            Dictionary {ticker: articles_list}
        """
        news_data = {}
        for ticker in tickers:
            articles = self.search_ticker_news(ticker, period_days=period_days)
            if articles:
                news_data[ticker] = articles

        logger.info(f"OK Fetched news for {len(news_data)}/{len(tickers)} tickers")
        return news_data

    @staticmethod
    def extract_article_features(article: Dict) -> Dict:
        """
        Extract useful features from a news article.

        Args:
            article: Article dictionary from NewsAPI

        Returns:
            Dictionary with extracted features
        """
        return {
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'content': article.get('content', ''),
            'source': article.get('source', {}).get('name', ''),
            'author': article.get('author', ''),
            'published_at': article.get('publishedAt', ''),
            'url': article.get('url', ''),
        }


# Convenience functions
def fetch_ticker_news(ticker: str) -> Optional[List[Dict]]:
    """Quick function to fetch news for a ticker."""
    collector = NewsDataCollector()
    return collector.search_ticker_news(ticker)


def fetch_macro_news() -> Optional[List[Dict]]:
    """Quick function to fetch macroeconomic news."""
    collector = NewsDataCollector()
    return collector.search_macro_news()


def fetch_batch_news(tickers: List[str]) -> Dict[str, List[Dict]]:
    """Quick function to fetch news for multiple tickers."""
    collector = NewsDataCollector()
    return collector.search_batch_news(tickers)

