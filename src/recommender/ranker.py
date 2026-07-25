"""Stock ranking and recommendation engine."""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from config.settings import ENSEMBLE_WEIGHTS, TOP_N_RECOMMENDATIONS

logger = logging.getLogger(__name__)


@dataclass
class StockScore:
    """Stock analysis score."""
    ticker: str
    technical_score: float
    sentiment_score: float
    overall_score: float
    analysis_date: str = None
    sector_momentum_bonus: float = 0.0
    earnings_risk_penalty: float = 0.0
    earnings_warning: bool = False
    next_earnings_date: Optional[str] = None

    def __post_init__(self):
        if self.analysis_date is None:
            self.analysis_date = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        d = {
            'ticker': self.ticker,
            'technical_score': round(self.technical_score, 1),
            'sentiment_score': round(self.sentiment_score, 1),
            'overall_score': round(self.overall_score, 1),
            'analysis_date': self.analysis_date,
            'sector_momentum_bonus': round(self.sector_momentum_bonus, 2),
            'earnings_risk_penalty': round(self.earnings_risk_penalty, 2),
        }
        if self.earnings_warning:
            d['earnings_warning'] = True
            if self.next_earnings_date:
                d['next_earnings_date'] = self.next_earnings_date
        return d


class StockRanker:
    """Rank stocks based on combined scores."""

    def __init__(
        self,
        technical_weight: float = ENSEMBLE_WEIGHTS['technical'],
        sentiment_weight: float = ENSEMBLE_WEIGHTS['sentiment']
    ):
        self.technical_weight = technical_weight
        self.sentiment_weight = sentiment_weight

        # Validate weights sum to 1.0
        total = technical_weight + sentiment_weight
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights don't sum to 1.0: {total}")

    def calculate_ensemble_score(
        self,
        technical_score: float,
        sentiment_score: float,
        sector_momentum_bonus: float = 0.0,
        earnings_risk_penalty: float = 0.0
    ) -> float:
        """
        Calculate ensemble score from technical and sentiment, with sector bonus and earnings penalty.

        Formula: ensemble = (technical * 0.6) + (sentiment * 0.4) + sector_bonus - earnings_penalty

        Args:
            technical_score: Technical indicator score (0-100)
            sentiment_score: Sentiment analysis score (0-100)
            sector_momentum_bonus: Bonus points from sector relative strength (default 0)
            earnings_risk_penalty: Penalty points from earnings risk (default 0)

        Returns:
            Ensemble score (0-100)
        """
        if pd.isna(technical_score):
            technical_score = 50.0
        if pd.isna(sentiment_score):
            sentiment_score = 50.0

        ensemble = (
            (technical_score * self.technical_weight) +
            (sentiment_score * self.sentiment_weight) +
            sector_momentum_bonus -
            earnings_risk_penalty
        )

        return min(100, max(0, ensemble))

    def rank_stocks(
        self,
        stock_scores: List[Tuple[str, float, float]],
        sector_bonuses: Optional[Dict[str, float]] = None,
        earnings_penalties: Optional[Dict[str, float]] = None,
        earnings_flags: Optional[Dict[str, Dict]] = None
    ) -> List[StockScore]:
        """
        Rank stocks by ensemble score, with sector bonus and earnings risk penalty.

        Args:
            stock_scores: List of (ticker, technical_score, sentiment_score) tuples
            sector_bonuses: Dict {ticker: bonus_points} (default None = no bonus)
            earnings_penalties: Dict {ticker: penalty_points} (default None = no penalty)
            earnings_flags: Dict {ticker: {'warning': bool, 'date': str}} (default None)

        Returns:
            Sorted list of StockScore objects
        """
        scores = []

        for ticker, tech_score, sent_score in stock_scores:
            bonus = (sector_bonuses or {}).get(ticker, 0.0)
            penalty = (earnings_penalties or {}).get(ticker, 0.0)
            earnings_info = (earnings_flags or {}).get(ticker, {})

            ensemble_score = self.calculate_ensemble_score(tech_score, sent_score, bonus, penalty)

            score = StockScore(
                ticker=ticker,
                technical_score=tech_score,
                sentiment_score=sent_score,
                overall_score=ensemble_score,
                sector_momentum_bonus=bonus,
                earnings_risk_penalty=penalty,
                earnings_warning=earnings_info.get('warning', False),
                next_earnings_date=earnings_info.get('date', None)
            )

            scores.append(score)

        # Sort by overall score (descending)
        scores.sort(key=lambda x: x.overall_score, reverse=True)

        return scores

    def get_top_recommendations(
        self,
        ranked_scores: List[StockScore],
        top_n: int = TOP_N_RECOMMENDATIONS
    ) -> List[StockScore]:
        """
        Extract top N recommendations.

        Args:
            ranked_scores: Ranked list of StockScore objects
            top_n: Number of recommendations to return

        Returns:
            Top N stocks
        """
        return ranked_scores[:top_n]

    def create_score_report(
        self,
        ranked_scores: List[StockScore],
        top_n: int = TOP_N_RECOMMENDATIONS
    ) -> Dict:
        """
        Create a report of top recommendations.

        Args:
            ranked_scores: Ranked list of StockScore objects
            top_n: Number of recommendations

        Returns:
            Report dictionary
        """
        top_stocks = self.get_top_recommendations(ranked_scores, top_n=top_n)

        report = {
            'timestamp': datetime.now().isoformat(),
            'total_analyzed': len(ranked_scores),
            'top_n': top_n,
            'recommendations': [score.to_dict() for score in top_stocks],
            'methodology': {
                'technical_weight': self.technical_weight,
                'sentiment_weight': self.sentiment_weight,
                'description': 'Ensemble score = (Technical × 60%) + (Sentiment × 40%)',
            }
        }

        return report

    @staticmethod
    def filter_by_score_threshold(
        ranked_scores: List[StockScore],
        min_score: float = 60.0
    ) -> List[StockScore]:
        """
        Filter stocks by minimum score threshold.

        Args:
            ranked_scores: Ranked list of StockScore objects
            min_score: Minimum overall score

        Returns:
            Filtered list
        """
        return [score for score in ranked_scores if score.overall_score >= min_score]

    @staticmethod
    def group_by_quality(ranked_scores: List[StockScore]) -> Dict[str, List[StockScore]]:
        """
        Group stocks by quality tier.

        Args:
            ranked_scores: Ranked list of StockScore objects

        Returns:
            Dictionary with tiers: excellent, good, fair, poor
        """
        tiers = {
            'excellent': [],  # 80+
            'good': [],       # 70-80
            'fair': [],       # 60-70
            'poor': []        # <60
        }

        for score in ranked_scores:
            if score.overall_score >= 80:
                tiers['excellent'].append(score)
            elif score.overall_score >= 70:
                tiers['good'].append(score)
            elif score.overall_score >= 60:
                tiers['fair'].append(score)
            else:
                tiers['poor'].append(score)

        return tiers

    @staticmethod
    def calculate_score_distribution(
        ranked_scores: List[StockScore]
    ) -> Dict:
        """
        Calculate distribution statistics of scores.

        Args:
            ranked_scores: Ranked list of StockScore objects

        Returns:
            Distribution statistics
        """
        if not ranked_scores:
            return {}

        scores_list = [s.overall_score for s in ranked_scores]

        return {
            'mean': round(sum(scores_list) / len(scores_list), 1),
            'min': round(min(scores_list), 1),
            'max': round(max(scores_list), 1),
            'median': round(sorted(scores_list)[len(scores_list) // 2], 1),
            'count': len(scores_list),
        }


def rank_and_recommend(
    stock_scores_dict: Dict[str, Tuple[float, float]],
    sector_bonuses: Optional[Dict[str, float]] = None,
    earnings_penalties: Optional[Dict[str, float]] = None,
    earnings_flags: Optional[Dict[str, Dict]] = None
) -> Dict:
    """
    Convenient function to rank stocks and get top recommendations.

    Args:
        stock_scores_dict: {ticker: (technical_score, sentiment_score)}
        sector_bonuses: {ticker: bonus_points} (optional)
        earnings_penalties: {ticker: penalty_points} (optional)
        earnings_flags: {ticker: {'warning': bool, 'date': str}} (optional)

    Returns:
        Recommendation report
    """
    ranker = StockRanker()

    # Convert dict to list
    stock_scores = [
        (ticker, tech_score, sent_score)
        for ticker, (tech_score, sent_score) in stock_scores_dict.items()
    ]

    # Rank
    ranked = ranker.rank_stocks(
        stock_scores,
        sector_bonuses=sector_bonuses,
        earnings_penalties=earnings_penalties,
        earnings_flags=earnings_flags
    )

    # Generate report
    report = ranker.create_score_report(ranked)

    # Add distribution stats
    report['score_distribution'] = ranker.calculate_score_distribution(ranked)

    # Add quality tiers
    tiers = ranker.group_by_quality(ranked)
    report['quality_tiers'] = {
        tier: [s.to_dict() for s in stocks]
        for tier, stocks in tiers.items()
    }

    return report
