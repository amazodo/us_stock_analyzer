"""Sentiment analysis and scoring from news."""

import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyze sentiment from news articles."""

    def __init__(self):
        try:
            from textblob import TextBlob
            self.textblob_available = True
        except ImportError:
            logger.warning("TextBlob not available for sentiment analysis")
            self.textblob_available = False

    def analyze_sentiment_textblob(self, text: str) -> Tuple[float, str]:
        """
        Analyze sentiment using TextBlob (VADER-like approach).

        Args:
            text: Text to analyze

        Returns:
            Tuple of (polarity_score, label)
            - polarity_score: -1 to 1 (negative to positive)
            - label: 'negative', 'neutral', 'positive'
        """
        if not self.textblob_available:
            return 0.0, 'neutral'

        try:
            from textblob import TextBlob

            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1

            if polarity < -0.1:
                label = 'negative'
            elif polarity > 0.1:
                label = 'positive'
            else:
                label = 'neutral'

            return polarity, label

        except Exception as e:
            logger.error(f"Error in TextBlob sentiment analysis: {e}")
            return 0.0, 'neutral'

    def analyze_articles_sentiment(
        self,
        articles: List[Dict],
        use_titles_only: bool = False
    ) -> Dict:
        """
        Analyze sentiment across multiple articles.

        Args:
            articles: List of news articles (from NewsAPI)
            use_titles_only: If True, analyze only titles; else use description + content

        Returns:
            Dictionary with sentiment analysis results
        """
        if not articles:
            return {
                'total_articles': 0,
                'average_sentiment': 0.0,
                'positive_count': 0,
                'neutral_count': 0,
                'negative_count': 0,
                'sentiment_label': 'neutral',
                'articles': []
            }

        sentiments = []

        for article in articles:
            # Extract text
            if use_titles_only:
                text = article.get('title', '')
            else:
                text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"

            if not text.strip():
                continue

            # Analyze
            polarity, label = self.analyze_sentiment_textblob(text)

            sentiments.append({
                'title': article.get('title', ''),
                'source': article.get('source', {}).get('name', '') if isinstance(article.get('source'), dict) else article.get('source', ''),
                'published_at': article.get('publishedAt', ''),
                'polarity': round(polarity, 3),
                'label': label,
                'url': article.get('url', '')
            })

        # Calculate aggregate sentiment
        if not sentiments:
            return {
                'total_articles': 0,
                'average_sentiment': 0.0,
                'positive_count': 0,
                'neutral_count': 0,
                'negative_count': 0,
                'sentiment_label': 'neutral',
                'articles': []
            }

        avg_sentiment = sum(s['polarity'] for s in sentiments) / len(sentiments)
        positive_count = sum(1 for s in sentiments if s['label'] == 'positive')
        neutral_count = sum(1 for s in sentiments if s['label'] == 'neutral')
        negative_count = sum(1 for s in sentiments if s['label'] == 'negative')

        # Overall label
        if avg_sentiment > 0.1:
            overall_label = 'positive'
        elif avg_sentiment < -0.1:
            overall_label = 'negative'
        else:
            overall_label = 'neutral'

        return {
            'total_articles': len(sentiments),
            'average_sentiment': round(avg_sentiment, 3),
            'positive_count': positive_count,
            'neutral_count': neutral_count,
            'negative_count': negative_count,
            'positive_ratio': round(positive_count / len(sentiments), 3),
            'sentiment_label': overall_label,
            'articles': sentiments
        }

    def convert_to_score(self, sentiment_result: Dict) -> float:
        """
        Convert sentiment analysis to 0-100 score.

        Args:
            sentiment_result: Result from analyze_articles_sentiment

        Returns:
            Score (0-100), where 50 is neutral
        """
        if not sentiment_result or sentiment_result.get('total_articles', 0) == 0:
            return 50.0

        avg_sentiment = sentiment_result.get('average_sentiment', 0.0)

        # Convert -1 to +1 range to 0-100 scale
        score = 50 + (avg_sentiment * 50)

        return min(100, max(0, score))

    def generate_sentiment_summary(self, sentiment_result: Dict) -> str:
        """
        Generate human-readable sentiment summary.

        Args:
            sentiment_result: Result from analyze_articles_sentiment

        Returns:
            Summary string
        """
        if not sentiment_result or sentiment_result.get('total_articles', 0) == 0:
            return "No news data available."

        total = sentiment_result.get('total_articles', 0)
        label = sentiment_result.get('sentiment_label', 'neutral')
        positive = sentiment_result.get('positive_count', 0)
        negative = sentiment_result.get('negative_count', 0)

        if label == 'positive':
            return f"🟢 Positive sentiment ({positive}/{total} positive articles)"
        elif label == 'negative':
            return f"🔴 Negative sentiment ({negative}/{total} negative articles)"
        else:
            return f"🟡 Neutral sentiment (balanced news coverage)"


class AICLaudeSentimentAnalyzer:
    """Advanced sentiment analysis using Claude API."""

    def __init__(self, api_key: str = None):
        try:
            from anthropic import Anthropic
            from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL

            self.client = Anthropic(api_key=api_key or ANTHROPIC_API_KEY)
            self.model = CLAUDE_MODEL
            self.available = bool(api_key or ANTHROPIC_API_KEY)
        except (ImportError, Exception) as e:
            logger.warning(f"Anthropic SDK not available or API key missing: {e}")
            self.available = False

    def analyze_with_claude(
        self,
        articles: List[Dict],
        ticker: str = "UNKNOWN"
    ) -> Dict:
        """
        Analyze sentiment using Claude API.

        Args:
            articles: List of news articles
            ticker: Stock ticker for context

        Returns:
            Sentiment analysis result
        """
        if not self.available:
            return {'error': 'Claude API not available'}

        if not articles:
            return {'sentiment': 'neutral', 'score': 50, 'analysis': 'No news data'}

        # Prepare article summaries for Claude
        article_texts = []
        for article in articles[:5]:  # Limit to top 5 articles
            title = article.get('title', '')
            desc = article.get('description', '')
            article_texts.append(f"- {title}: {desc}")

        articles_str = '\n'.join(article_texts)

        prompt = f"""Analyze the sentiment of these news articles about {ticker} stock.

Articles:
{articles_str}

Provide:
1. Overall sentiment (positive/neutral/negative)
2. Confidence score (0-100)
3. Key themes
4. Impact on stock price prediction

Keep response concise and actionable."""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-1",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis_text = response.content[0].text

            return {
                'sentiment': 'pending',  # Would parse from response
                'analysis': analysis_text,
                'articles_analyzed': len(articles)
            }

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return {'error': str(e)}

    def analyze_expert_opinion(
        self,
        ticker: str,
        articles: List[Dict]
    ) -> Dict:
        """
        Analyze expert opinion on a stock's 1-week direction using Claude.
        Returns a structured score (0-100) with 0=strong bearish, 50=neutral, 100=strong bullish.

        Args:
            ticker: Stock ticker
            articles: News articles for context

        Returns:
            Dictionary with:
              - 'score': float (0-100), 50.0 default if any failure
              - 'analysis': str (Claude's response text)
              - 'parsed': bool (whether score was successfully parsed)
        """
        if not self.available or not articles:
            return {
                'score': 50.0,
                'analysis': '',
                'parsed': False
            }

        # Prepare article summaries for Claude
        article_bullets = []
        for article in articles[:5]:  # Limit to top 5 for context
            title = article.get('title', '')
            desc = article.get('description', '')
            if title:
                article_bullets.append(f"- {title}: {desc[:100] if desc else '(no description)'}")

        articles_str = '\n'.join(article_bullets) if article_bullets else "(No articles available)"

        prompt = f"""You are a senior equity analyst. Based on the following recent news about {ticker},
give your 1-week directional conviction as a single integer 0-100, where:
- 0 = strong bearish conviction
- 50 = neutral / no conviction either way
- 100 = strong bullish conviction

Consider catalysts, risks, market context, and technical setup implications.

News about {ticker}:
{articles_str}

Respond with:
1. A 2-3 sentence analysis/reasoning
2. Then end with EXACTLY one line: SCORE: <integer>

Example:
"The company beat earnings expectations and raised guidance.
Analyst upgrades are rolling in. Strong momentum should continue."
SCORE: 82"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis_text = response.content[0].text

            # Parse SCORE: <integer> from response
            match = re.search(r'SCORE:\s*(\d{1,3})', analysis_text, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                # Clamp to 0-100
                score = min(100.0, max(0.0, score))
                return {
                    'score': score,
                    'analysis': analysis_text,
                    'parsed': True
                }
            else:
                # No SCORE line found, return neutral with unparsed flag
                logger.warning(f"Could not parse SCORE line from Claude response for {ticker}")
                return {
                    'score': 50.0,
                    'analysis': analysis_text,
                    'parsed': False
                }

        except Exception as e:
            logger.error(f"Error calling Claude API for expert opinion on {ticker}: {e}")
            return {
                'score': 50.0,
                'analysis': '',
                'parsed': False
            }


def analyze_ticker_sentiment(
    ticker: str,
    articles: List[Dict],
    use_claude: bool = False
) -> Dict:
    """
    Comprehensive sentiment analysis for a ticker.

    Args:
        ticker: Stock ticker
        articles: News articles
        use_claude: Whether to use Claude for advanced analysis

    Returns:
        Sentiment analysis result
    """
    # Basic sentiment
    analyzer = SentimentAnalyzer()
    basic_sentiment = analyzer.analyze_articles_sentiment(articles)
    basic_score = analyzer.convert_to_score(basic_sentiment)

    result = {
        'ticker': ticker,
        'timestamp': datetime.now().isoformat(),
        'basic_sentiment': basic_sentiment,
        'technical_score': basic_score,
        'summary': analyzer.generate_sentiment_summary(basic_sentiment),
    }

    # Advanced Claude analysis
    if use_claude:
        claude_analyzer = AICLaudeSentimentAnalyzer()
        claude_result = claude_analyzer.analyze_with_claude(articles, ticker)
        result['claude_analysis'] = claude_result

    return result


def calculate_qualitative_score(
    ticker: str,
    macro_articles: List[Dict],
    ticker_articles: List[Dict],
    use_expert_opinion: bool = None
) -> Tuple[float, Dict]:
    """
    Calculate qualitative (sentiment) score using 3-part weighting:
    - Macro news (30%): broad market/economic news sentiment
    - Ticker news (40%): company-specific news sentiment
    - Expert opinion (30%): Claude-based directional conviction

    Args:
        ticker: Stock ticker
        macro_articles: List of macro/economic news articles
        ticker_articles: List of company-specific news articles
        use_expert_opinion: Whether to include Claude expert opinion
                           Default: uses config.EXPERT_OPINION_ENABLED

    Returns:
        Tuple of (overall_qual_score, detail_dict)
    """
    from config.settings import QUAL_WEIGHTS, EXPERT_OPINION_ENABLED

    if use_expert_opinion is None:
        use_expert_opinion = EXPERT_OPINION_ENABLED

    analyzer = SentimentAnalyzer()

    # Score macro news
    macro_sentiment = analyzer.analyze_articles_sentiment(macro_articles) if macro_articles else {}
    macro_score = analyzer.convert_to_score(macro_sentiment)

    # Score ticker news
    ticker_sentiment = analyzer.analyze_articles_sentiment(ticker_articles) if ticker_articles else {}
    ticker_score = analyzer.convert_to_score(ticker_sentiment)

    # Get expert opinion
    if use_expert_opinion:
        claude_analyzer = AICLaudeSentimentAnalyzer()
        # Use ticker articles for expert opinion context
        expert_result = claude_analyzer.analyze_expert_opinion(ticker, ticker_articles)
        expert_score = expert_result.get('score', 50.0)
    else:
        expert_result = {'score': 50.0, 'analysis': '', 'parsed': False}
        expert_score = 50.0

    # Apply QUAL_WEIGHTS (macro 30, ticker 40, expert 30)
    weights = QUAL_WEIGHTS
    qual_score = (
        macro_score * (weights.get('macro', 30) / 100.0) +
        ticker_score * (weights.get('ticker', 40) / 100.0) +
        expert_score * (weights.get('expert', 30) / 100.0)
    )

    detail_dict = {
        'macro_score': round(macro_score, 1),
        'macro_article_count': len(macro_articles) if macro_articles else 0,
        'ticker_score': round(ticker_score, 1),
        'ticker_article_count': len(ticker_articles) if ticker_articles else 0,
        'expert_score': round(expert_score, 1),
        'expert_opinion': expert_result,
        'weights': weights
    }

    return round(qual_score, 1), detail_dict
