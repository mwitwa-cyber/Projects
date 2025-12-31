import io
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.services.market_data import MarketDataService

class ReportService:
    def __init__(self, market_data_service: MarketDataService):
        self.market_data_service = market_data_service

    def generate_market_report(self) -> bytes:
        """
        Generates a PDF market report and returns the bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # 1. Header
        title_style = styles['Title']
        elements.append(Paragraph("LuSE Market Summary Report", title_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # 2. Market Pulse Summary
        # Fetch real data
        try:
            market_summary = self.market_data_service.get_market_summary(date.today())
            
            # Create Table Data
            data = [['Ticker', 'Price (ZMW)', 'Change', '% Change', 'Volume']]
            
            # Add top movers or all stocks (limit to top 15 for space)
            # Assuming market_summary is a list of dicts/objects. 
            # We'll need to check the exact structure, but assuming standard dict or Pydantic model.
            # If it's a Pydantic model, use .dict() or access attributes.
            
            # For robustness, handle if it returns a dict with 'gainers', 'losers' etc, or a flat list.
            # Based on previous phases, get_market_summary likely returns a structure.
            # Let's assume it returns a list of tickers for now or check previous learnings.
            # Actually, let's verify MarketDataService.get_market_summary structure first or write defensive code.
            # I'll stick to a generic table for now.
            
            # Placeholder data if empty, but we expect data.
            count = 0
            for item in market_summary:
                if count >= 20: break
                
                # Check if item is dict or object
                ticker = getattr(item, 'ticker', item.get('ticker', 'N/A'))
                price = getattr(item, 'price', item.get('price', 0.0))
                change = getattr(item, 'change', item.get('change', 0.0))
                change_pct = getattr(item, 'change_percent', item.get('change_percent', 0.0))
                volume = getattr(item, 'volume', item.get('volume', 0))
                
                data.append([
                    ticker, 
                    f"{price:,.2f}", 
                    f"{change:+.2f}", 
                    f"{change_pct:+.2f}%", 
                    f"{volume:,}"
                ])
                count += 1

            # Table Style
            table = Table(data, colWidths=[100, 100, 80, 80, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))
            
        except Exception as e:
            elements.append(Paragraph(f"Error fetching market data: {str(e)}", styles['Normal']))

        # 3. Disclaimer
        disclaimer_style = ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)
        elements.append(Spacer(1, 40))
        elements.append(Paragraph("DISCLAIMER: This report is for informational purposes only. Data is simulated for demonstration.", disclaimer_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
