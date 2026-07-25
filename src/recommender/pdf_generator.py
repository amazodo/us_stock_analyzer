"""PDF report generation using reportlab."""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    Image, KeepTogether
)

from config.settings import OUTPUT_DIR, TARGET_GAIN_PERCENT

logger = logging.getLogger(__name__)


def generate_pdf_report(
    top_stocks: List[Dict],
    ranking_report: Dict,
    analysis_details: Optional[Dict] = None,
    output_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Generate a PDF report from analysis data.

    Args:
        top_stocks: List of top recommendation dicts (with scores, etc.)
        ranking_report: Ranking report dict (with methodology, etc.)
        analysis_details: Optional detailed analysis data
        output_path: Path to save PDF (default: outputs/top5_recommendations_<timestamp>.pdf)

    Returns:
        Path to saved PDF file, or None if error
    """
    try:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            output_path = OUTPUT_DIR / f"top5_recommendations_{timestamp}.pdf"

        # Create document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )

        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=6,
            alignment=1  # CENTER
        )
        story.append(Paragraph("US Stock AI Analyzer", title_style))
        story.append(Paragraph("Top 5 Recommendations", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))

        # Metadata
        metadata_style = ParagraphStyle(
            'Metadata',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666')
        )
        analysis_date = ranking_report.get('timestamp', 'Unknown')
        story.append(Paragraph(f"<b>Analysis Date:</b> {analysis_date}", metadata_style))
        story.append(Paragraph(f"<b>Target Gain:</b> {TARGET_GAIN_PERCENT}% in 1 week", metadata_style))
        story.append(Spacer(1, 0.3*inch))

        # Top 5 Recommendations Table
        story.append(Paragraph("Top 5 Recommendations", styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))

        # Build table data
        table_data = [['Rank', 'Ticker', 'Overall Score', 'Tech Score', 'Sentiment']]

        for idx, stock in enumerate(top_stocks[:5], 1):
            ticker = stock.get('ticker', 'N/A')
            overall = round(stock.get('overall_score', 0), 1)
            technical = round(stock.get('technical_score', 0), 1)
            sentiment = round(stock.get('sentiment_score', 0), 1)

            table_data.append([
                str(idx),
                ticker,
                f"{overall}",
                f"{technical}",
                f"{sentiment}"
            ])

        table = Table(table_data, colWidths=[0.8*inch, 1.0*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
        ]))

        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # Methodology
        story.append(Paragraph("Methodology", styles['Heading3']))
        methodology = ranking_report.get('methodology', {})
        tech_weight = methodology.get('technical_weight', 0.60)
        sent_weight = methodology.get('sentiment_weight', 0.40)

        methodology_text = f"""
        <b>Scoring Formula:</b><br/>
        Final Score = (Technical Indicators × {int(tech_weight*100)}%) + (Sentiment Analysis × {int(sent_weight*100)}%)<br/>
        <br/>
        <b>Technical Indicators (100 points):</b><br/>
        • Moving Averages (30 points): SMA 20/50/200, EMA 12/26<br/>
        • Momentum (20 points): RSI, MACD, Stochastic<br/>
        • Volatility (20 points): Bollinger Bands, ATR, Volatility Measures<br/>
        • Volume & Flow (20 points): OBV, VWAP, Volume Spike, Institutional Flow<br/>
        • Fibonacci (10 points): Retracement Levels<br/>
        <br/>
        <b>Sentiment Analysis:</b><br/>
        • Macro News (30%): Economic indicators, market sentiment<br/>
        • Ticker News (40%): Company-specific news, earnings, analyst upgrades<br/>
        • Expert Opinion (30%): AI-based directional conviction (Claude)<br/>
        <br/>
        <b>Risk Filters:</b><br/>
        • ATR Volatility: Excludes stocks without sufficient volatility for 5% weekly move<br/>
        • Earnings Risk: Flags stocks with earnings announcement within 7 days<br/>
        <br/>
        """

        story.append(Paragraph(methodology_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        # Disclaimer
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=0  # LEFT
        )
        disclaimer_text = """
        <b>DISCLAIMER:</b> This analysis is for informational purposes only and should not be considered as financial advice.
        Past performance is not indicative of future results. Trading stocks involves risk of loss. Always conduct your own
        research and consult with a financial advisor before making investment decisions. The AI-generated recommendations
        are based on historical data and may not accurately predict future price movements.
        """
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        # Build PDF
        doc.build(story)
        logger.info(f"OK PDF report saved: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        return None


def generate_pdf_report_to_bytes(
    top_stocks: List[Dict],
    ranking_report: Dict,
    analysis_details: Optional[Dict] = None
) -> Optional[bytes]:
    """
    Generate a PDF report to bytes (for Streamlit download).

    Args:
        top_stocks: List of top recommendation dicts
        ranking_report: Ranking report dict
        analysis_details: Optional detailed analysis data

    Returns:
        PDF bytes, or None if error
    """
    try:
        # Create in-memory file
        pdf_buffer = BytesIO()

        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )

        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=6,
            alignment=1  # CENTER
        )
        story.append(Paragraph("US Stock AI Analyzer", title_style))
        story.append(Paragraph("Top 5 Recommendations", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))

        # Metadata
        metadata_style = ParagraphStyle(
            'Metadata',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666')
        )
        analysis_date = ranking_report.get('timestamp', 'Unknown')
        story.append(Paragraph(f"<b>Analysis Date:</b> {analysis_date}", metadata_style))
        story.append(Paragraph(f"<b>Target Gain:</b> {TARGET_GAIN_PERCENT}% in 1 week", metadata_style))
        story.append(Spacer(1, 0.3*inch))

        # Top 5 Recommendations Table
        story.append(Paragraph("Top 5 Recommendations", styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))

        # Build table data
        table_data = [['Rank', 'Ticker', 'Overall Score', 'Tech Score', 'Sentiment']]

        for idx, stock in enumerate(top_stocks[:5], 1):
            ticker = stock.get('ticker', 'N/A')
            overall = round(stock.get('overall_score', 0), 1)
            technical = round(stock.get('technical_score', 0), 1)
            sentiment = round(stock.get('sentiment_score', 0), 1)

            table_data.append([
                str(idx),
                ticker,
                f"{overall}",
                f"{technical}",
                f"{sentiment}"
            ])

        table = Table(table_data, colWidths=[0.8*inch, 1.0*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
        ]))

        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # Disclaimer
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=0  # LEFT
        )
        disclaimer_text = """
        <b>DISCLAIMER:</b> This analysis is for informational purposes only. Past performance does not guarantee future results.
        Always consult with a financial advisor before making investment decisions.
        """
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        # Build PDF
        doc.build(story)

        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    except Exception as e:
        logger.error(f"Error generating PDF to bytes: {e}")
        return None

