"""Generate final recommendation reports."""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from config.settings import OUTPUT_DIR, TARGET_GAIN_PERCENT

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate markdown reports from analysis results."""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_top_5_report(
        self,
        top_stocks: List[Dict],
        ranking_report: Dict,
        analysis_details: Dict = None,
        news_data: Dict = None
    ) -> str:
        """
        Generate top 5 stock recommendations report in Markdown.

        Args:
            top_stocks: List of top 5 stock data dicts
            ranking_report: Ranking report from ranker
            analysis_details: Detailed analysis per stock

        Returns:
            Markdown string
        """
        today = datetime.now().strftime("%Y-%m-%d_%H%M")

        # Header
        md = "# 📊 Weekly Top 5 Stock Recommendations\n\n"
        md += f"**Analysis Date**: {today}\n"
        md += f"**Target Gain**: {TARGET_GAIN_PERCENT}% in 1 week\n"
        md += f"**Methodology**: Technical Analysis Only (6 indicators)\n\n"

        # Summary stats
        if ranking_report and 'score_distribution' in ranking_report:
            dist = ranking_report['score_distribution']
            md += "## 📈 Market Overview\n\n"
            md += f"- **Stocks Analyzed**: {dist.get('count', 0)}\n"
            md += f"- **Average Score**: {dist.get('mean', 0)}/100\n"
            md += f"- **Score Range**: {dist.get('min', 0)} - {dist.get('max', 0)}\n\n"

        # Top 5 recommendations
        md += "## 🏆 Top 5 Recommendations\n\n"

        for rank, stock in enumerate(top_stocks, 1):
            ticker = stock.get('ticker', 'UNKNOWN')
            tech_score = stock.get('technical_score', 0)
            overall = stock.get('overall_score', 0)

            md += f"### #{rank}. {ticker}\n\n"
            md += f"**Overall Score**: {overall}/100\n"
            md += f"- **Technical Score**: {tech_score}/100\n\n"

            # Add detailed analysis if available
            if analysis_details and ticker in analysis_details:
                details = analysis_details[ticker]

                # Technical analysis
                if 'technical_details' in details:
                    tech = details['technical_details']
                    md += f"**Technical Analysis**\n"
                    md += f"- Trend: {tech.get('trend', 'N/A')}\n"
                    md += f"- RSI: {tech.get('rsi', 'N/A')}\n"
                    md += f"- MACD: {tech.get('macd_signal', 'N/A')}\n\n"

            # Price target
            md += f"**1-Week Price Target**: +{TARGET_GAIN_PERCENT}% upside\n\n"

            # Recent news
            if news_data and ticker in news_data:
                articles = news_data.get(ticker, [])
                if articles:
                    md += f"**Recent News**\n"
                    for article in articles[:3]:
                        title = article.get('title', 'N/A')
                        url = article.get('url', '#')
                        md += f"- [{title}]({url})\n"
                    md += "\n"

            # Risk factors based on score and market conditions
            risks = []

            # Low score risk
            if tech_score < 50:
                risks.append("⚠️ Low technical score (weak signal)")

            # High volatility risk
            if tech_score > 75 and overall > 70:
                risks.append("📈 High momentum (take profits early)")

            # No news risk
            if not (news_data and ticker in news_data):
                risks.append("📰 Limited news coverage (low media attention)")

            # Mid-range risk
            if 50 <= tech_score < 65:
                risks.append("⚖️ Mixed signals (wait for confirmation)")

            # Display risks
            if risks:
                md += f"**Key Risks**\n"
                for risk in risks:
                    md += f"- {risk}\n"
                md += "\n"
            else:
                md += f"**Key Risks**: No significant risks identified\n\n"

            md += "---\n\n"

        # Disclaimer
        md += "## ⚠️ Disclaimer\n\n"
        md += "This report is for educational purposes only and should not be considered as financial advice. "
        md += "Always conduct your own research and consult with a financial advisor before making investment decisions. "
        md += "Past performance does not guarantee future results.\n\n"

        # Methodology
        md += "## 📋 Methodology\n\n"
        md += "### Score Components\n\n"
        md += "**6 Technical Indicators**\n"
        md += "- Moving Averages (SMA/EMA trends) - 24%\n"
        md += "- Momentum (RSI, MACD, Stochastic) - 16%\n"
        md += "- Volatility (Bollinger Bands, ATR) - 16%\n"
        md += "- Volume/Flow (OBV, VWAP, MFI) - 16%\n"
        md += "- Fibonacci Retracement Levels - 8%\n"
        md += "- **Ichimoku Cloud (NEW)** - 20%\n\n"

        # Generated timestamp
        md += f"*Report generated: {datetime.now().isoformat()}*\n"

        return md

    def generate_detailed_analysis_report(
        self,
        ticker: str,
        analysis_data: Dict
    ) -> str:
        """
        Generate detailed single-stock analysis report.

        Args:
            ticker: Stock ticker
            analysis_data: Detailed analysis dictionary

        Returns:
            Markdown string
        """
        md = f"# {ticker} - Detailed Analysis\n\n"
        md += f"**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Scores
        md += "## Technical Score Breakdown\n\n"
        md += f"- **Overall Score**: {analysis_data.get('overall_score', 0)}/100\n"
        md += f"- **Technical Score**: {analysis_data.get('technical_score', 0)}/100\n\n"

        # Technical breakdown
        if 'technical_components' in analysis_data:
            md += "## Technical Indicator Scores\n\n"
            components = analysis_data['technical_components']
            indicator_names = {
                'moving_averages': 'Moving Averages (SMA/EMA Trends)',
                'momentum': 'Momentum (RSI/MACD/Stochastic)',
                'volatility': 'Volatility (Bollinger Bands/ATR)',
                'volume_flow': 'Volume & Flow (OBV/VWAP/MFI)',
                'fibonacci': 'Fibonacci Retracement Levels',
                'ichimoku': 'Ichimoku Cloud (NEW)',
            }
            for component, score in components.items():
                label = indicator_names.get(component, component.title())
                md += f"- **{label}**: {score}/100\n"
            md += "\n"

        # Current metrics
        if 'current_metrics' in analysis_data:
            md += "## Current Price & Metrics\n\n"
            metrics = analysis_data['current_metrics']
            for metric, value in metrics.items():
                md += f"- **{metric.replace('_', ' ').title()}**: {value}\n"
            md += "\n"

        # Indicators - Enhanced display
        if 'indicators' in analysis_data:
            md += "## Technical Indicator Details\n\n"
            indicators = analysis_data['indicators']

            # Group indicators by category
            ma_indicators = {k: v for k, v in indicators.items() if any(x in k.lower() for x in ['sma', 'ema', 'vwap', 'ma'])}
            momentum_indicators = {k: v for k, v in indicators.items() if any(x in k.lower() for x in ['rsi', 'macd', 'stoch'])}
            volatility_indicators = {k: v for k, v in indicators.items() if any(x in k.lower() for x in ['bb', 'atr', 'band', 'volatil'])}
            volume_indicators = {k: v for k, v in indicators.items() if any(x in k.lower() for x in ['obv', 'mfi', 'volume'])}

            if ma_indicators:
                md += "**Moving Averages & Trends:**\n"
                for indicator, value in ma_indicators.items():
                    md += f"- {indicator.replace('_', ' ').title()}: {value}\n"
                md += "\n"

            if momentum_indicators:
                md += "**Momentum Indicators:**\n"
                for indicator, value in momentum_indicators.items():
                    md += f"- {indicator.replace('_', ' ').title()}: {value}\n"
                md += "\n"

            if volatility_indicators:
                md += "**Volatility Indicators:**\n"
                for indicator, value in volatility_indicators.items():
                    md += f"- {indicator.replace('_', ' ').title()}: {value}\n"
                md += "\n"

            if volume_indicators:
                md += "**Volume & Flow:**\n"
                for indicator, value in volume_indicators.items():
                    md += f"- {indicator.replace('_', ' ').title()}: {value}\n"
                md += "\n"

        # Fibonacci levels
        if 'fibonacci_levels' in analysis_data:
            md += "## Fibonacci Support/Resistance Levels\n\n"
            fib = analysis_data['fibonacci_levels']
            if isinstance(fib, dict):
                for level, price in fib.items():
                    md += f"- {level}: ${price}\n"
                md += "\n"

        # Analysis summary
        md += "## Analysis Summary\n\n"
        md += "This analysis uses a **6-indicator technical ensemble** to identify stocks with the highest probability of 5%+ gain within 1 week:\n\n"
        md += "1. **Moving Averages (24%)** - Price position relative to short/medium/long-term trends (SMA 20/50/200, EMA 12/26)\n"
        md += "2. **Momentum (16%)** - Overbought/oversold conditions and trend confirmation (RSI 14, MACD, Stochastic)\n"
        md += "3. **Volatility (16%)** - Price range and standard deviation (Bollinger Bands, ATR)\n"
        md += "4. **Volume & Flow (16%)** - Institutional interest and supply/demand (OBV, VWAP, Money Flow Index)\n"
        md += "5. **Fibonacci (8%)** - Key support/resistance from swing highs/lows\n"
        md += "6. **Ichimoku Cloud (20%)** - Advanced trend confirmation via cloud position and crossovers\n\n"
        md += "**Risk Disclaimers:**\n"
        md += "- Technical analysis does not guarantee returns; past performance is not indicative of future results\n"
        md += "- Market conditions, earnings announcements, and macro events can override technical signals\n"
        md += "- Consider consulting a financial advisor before making investment decisions\n\n"

        return md

    def save_report(
        self,
        content: str,
        filename: str,
        extension: str = "md"
    ) -> Optional[Path]:
        """
        Save report to file.

        Args:
            content: Report content
            filename: Base filename (without extension)
            extension: File extension (default: md)

        Returns:
            Path to saved file or None if error
        """
        try:
            filepath = self.output_dir / f"{filename}.{extension}"

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"OK Report saved: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return None

    def save_json_report(
        self,
        data: Dict,
        filename: str
    ) -> Optional[Path]:
        """
        Save analysis data as JSON.

        Args:
            data: Dictionary to save
            filename: Base filename

        Returns:
            Path to saved file or None
        """
        import json

        try:
            filepath = self.output_dir / f"{filename}.json"

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"OK JSON report saved: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving JSON report: {e}")
            return None


def generate_weekly_report(
    top_stocks: List[Dict],
    ranking_report: Dict,
    analysis_details: Dict = None,
    output_dir: Path = OUTPUT_DIR,
    news_data: Dict = None
) -> Dict:
    """
    Generate and save weekly recommendation report.

    Args:
        top_stocks: List of top 5 stocks
        ranking_report: Ranking report
        analysis_details: Detailed analysis per stock
        output_dir: Output directory
        news_data: News articles per ticker

    Returns:
        Dictionary with generated file paths
    """
    generator = ReportGenerator(output_dir=output_dir)
    today = datetime.now().strftime("%Y-%m-%d")

    # Extract top news from ranking report if available
    if 'top_news' not in ranking_report and not news_data:
        news_data = ranking_report.get('top_news', {})

    # Generate markdown report
    md_content = generator.generate_top_5_report(
        top_stocks,
        ranking_report,
        analysis_details,
        news_data=news_data
    )

    # Save files
    md_path = generator.save_report(
        md_content,
        f"top5_recommendations_{today}",
        extension="md"
    )

    json_path = generator.save_json_report(
        ranking_report,
        f"analysis_data_{today}"
    )

    return {
        'markdown_report': md_path,
        'json_report': json_path,
        'timestamp': datetime.now().isoformat(),
    }

