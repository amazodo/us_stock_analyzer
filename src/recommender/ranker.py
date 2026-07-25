"""Stock ranking engine - Technical Analysis Only."""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class StockScore:
    """Stock analysis score (Technical only)."""
    ticker: str
    technical_score: float
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
        import math

        # Handle NaN values
        tech_score = 0.0 if math.isnan(self.technical_score) else self.technical_score
        overall_score = 0.0 if math.isnan(self.overall_score) else self.overall_score
        sector_bonus = 0.0 if math.isnan(self.sector_momentum_bonus) else self.sector_momentum_bonus
        earnings_penalty = 0.0 if math.isnan(self.earnings_risk_penalty) else self.earnings_risk_penalty

        d = {
            'ticker': self.ticker,
            'technical_score': round(tech_score, 1),
            'overall_score': round(overall_score, 1),
            'analysis_date': self.analysis_date,
            'sector_momentum_bonus': round(sector_bonus, 2),
            'earnings_risk_penalty': round(earnings_penalty, 2),
        }
        if self.earnings_warning:
            d['earnings_warning'] = True
            if self.next_earnings_date:
                d['next_earnings_date'] = self.next_earnings_date
        return d


class StockRanker:
    """Rank stocks based on technical scores only (100%)."""

    def __init__(self):
        logger.info("StockRanker initialized with Technical Analysis Only (100%)")

    def calculate_final_score(
        self,
        technical_score: float,
        sector_momentum_bonus: float = 0.0,
        earnings_risk_penalty: float = 0.0
    ) -> float:
        """
        Calculate final score from technical analysis with adjustments.

        Formula: final_score = technical_score + sector_bonus - earnings_penalty

        Args:
            technical_score: Technical indicator score (0-100)
            sector_momentum_bonus: Bonus points from sector relative strength (0-5)
            earnings_risk_penalty: Penalty points from earnings risk (0-5)

        Returns:
            Final score (0-100)
        """
        import math

        # Handle NaN values (convert to 0)
        technical_score = 0.0 if math.isnan(technical_score) else technical_score
        sector_momentum_bonus = 0.0 if math.isnan(sector_momentum_bonus) else sector_momentum_bonus
        earnings_risk_penalty = 0.0 if math.isnan(earnings_risk_penalty) else earnings_risk_penalty

        final_score = (
            technical_score +
            sector_momentum_bonus -
            earnings_risk_penalty
        )
        return min(100, max(0, final_score))

    def rank_stocks(
        self,
        stock_scores: List[Tuple[str, float]],
        sector_bonuses: Optional[Dict[str, float]] = None,
        earnings_penalties: Optional[Dict[str, float]] = None,
        earnings_flags: Optional[Dict[str, Dict]] = None
    ) -> List[StockScore]:
        """
        Rank stocks by technical score with adjustments.

        Args:
            stock_scores: List of (ticker, technical_score) tuples
            sector_bonuses: Dict {ticker: bonus_points}
            earnings_penalties: Dict {ticker: penalty_points}
            earnings_flags: Dict {ticker: {'warning': bool, 'date': str}}

        Returns:
            Sorted list of StockScore objects
        """
        import math

        scores = []

        for ticker, tech_score in stock_scores:
            bonus = (sector_bonuses or {}).get(ticker, 0.0)
            penalty = (earnings_penalties or {}).get(ticker, 0.0)
            earnings_info = (earnings_flags or {}).get(ticker, {})

            # Handle NaN values
            bonus = 0.0 if math.isnan(bonus) else bonus
            penalty = 0.0 if math.isnan(penalty) else penalty

            final_score = self.calculate_final_score(tech_score, bonus, penalty)

            score = StockScore(
                ticker=ticker,
                technical_score=tech_score,
                overall_score=final_score,
                sector_momentum_bonus=bonus,
                earnings_risk_penalty=penalty,
                earnings_warning=earnings_info.get('warning', False),
                next_earnings_date=earnings_info.get('next_earnings_date'),
            )
            scores.append(score)

        # Sort by overall score descending
        return sorted(scores, key=lambda x: x.overall_score, reverse=True)

    def create_score_report(self, ranked_stocks: List[StockScore]) -> Dict:
        """
        Create ranking report from ranked stocks.

        Args:
            ranked_stocks: Sorted list of StockScore objects

        Returns:
            Dictionary with report data
        """
        if not ranked_stocks:
            return {
                'recommendations': [],
                'methodology': 'Technical Analysis Only (100%)',
            }

        recommendations = [s.to_dict() for s in ranked_stocks]

        return {
            'recommendations': recommendations,
            'methodology': 'Technical Analysis Only (100%)',
            'analysis_date': datetime.now().isoformat(),
        }

    def calculate_score_distribution(self, ranked_stocks: List[StockScore]) -> Dict:
        """Calculate distribution statistics."""
        if not ranked_stocks:
            return {}

        scores = [s.overall_score for s in ranked_stocks]
        return {
            'mean': round(sum(scores) / len(scores), 1),
            'min': round(min(scores), 1),
            'max': round(max(scores), 1),
            'median': round(sorted(scores)[len(scores) // 2], 1),
            'count': len(scores),
        }

    def group_by_quality(self, ranked_stocks: List[StockScore]) -> Dict[str, List[StockScore]]:
        """Group stocks by quality tier."""
        tiers = {
            'Strong': [],
            'Good': [],
            'Neutral': [],
            'Weak': []
        }

        for stock in ranked_stocks:
            if stock.overall_score >= 75:
                tiers['Strong'].append(stock)
            elif stock.overall_score >= 60:
                tiers['Good'].append(stock)
            elif stock.overall_score >= 40:
                tiers['Neutral'].append(stock)
            else:
                tiers['Weak'].append(stock)

        return tiers


def rank_and_recommend(
    stock_scores_dict: Dict[str, float],
    sector_bonuses: Optional[Dict[str, float]] = None,
    earnings_penalties: Optional[Dict[str, float]] = None,
    earnings_flags: Optional[Dict[str, Dict]] = None
) -> Dict:
    """
    Rank stocks and generate recommendations.

    Args:
        stock_scores_dict: {ticker: technical_score}
        sector_bonuses: {ticker: bonus_points}
        earnings_penalties: {ticker: penalty_points}
        earnings_flags: {ticker: {'warning': bool, 'date': str}}

    Returns:
        Recommendation report dictionary
    """
    ranker = StockRanker()

    # Convert dict to list
    stock_scores = [
        (ticker, tech_score)
        for ticker, tech_score in stock_scores_dict.items()
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
