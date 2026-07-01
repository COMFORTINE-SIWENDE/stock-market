"""Email notification service for NSE Stock Market Analytics"""

from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Optional, List, Dict

from app.config.config import settings

logger = logging.getLogger(__name__)

class StockEmailService:
    """Email service for stock market notifications with dashboard theme"""
    
    def __init__(self):
        self.smtp_server = settings.EMAIL_HOST
        self.smtp_port = settings.EMAIL_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.use_tls = settings.EMAIL_USE_TLS
        self.use_ssl = settings.EMAIL_USE_SSL
        self.from_email = settings.EMAIL_FROM
        self.from_name = getattr(settings, 'EMAIL_FROM_NAME', 'NSE Stock Market System')
        
    def _get_connection(self):
        """Return SMTP connection"""
        if self.use_ssl:
            return smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30)
        else:
            return smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send HTML email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))

            with self._get_connection() as server:
                if self.use_tls and not self.use_ssl:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_daily_analytics_email(self, to_email: str, analytics_data: Dict) -> bool:
        """Send daily analytics report"""
        subject = f"📊 Daily NSE Analytics - {date.today().strftime('%B %d, %Y')}"
        body = self._create_analytics_template(analytics_data)
        return self.send_email(to_email, subject, body)

    def send_stock_alert_email(self, to_email: str, symbol: str, alert_type: str, 
                               message: str, current_price: float, predicted_price: Optional[float] = None) -> bool:
        """Send stock alert"""
        subject = f"🔔 Stock Alert: {symbol} - {alert_type}"
        body = self._create_alert_template(symbol, alert_type, message, current_price, predicted_price)
        return self.send_email(to_email, subject, body)

    def send_news_digest_email(self, to_email: str, news_articles: List[Dict]) -> bool:
        """Send news digest"""
        subject = f"📰 NSE News Digest - {date.today().strftime('%B %d, %Y')}"
        body = self._create_news_template(news_articles)
        return self.send_email(to_email, subject, body)

    def _get_header_html(self, title: str, subtitle: str = "") -> str:
        """Reusable header with dashboard theme"""
        if not subtitle:
            subtitle = date.today().strftime('%B %d, %Y')
        
        return f"""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 40px 30px; text-align: center;">
            <svg width="50" height="50" viewBox="0 0 40 40" style="margin-bottom: 15px;">
                <rect width="8" height="30" x="5" y="10" fill="#10b981" rx="2"/>
                <rect width="8" height="20" x="16" y="20" fill="#10b981" rx="2"/>
                <rect width="8" height="35" x="27" y="5" fill="#10b981" rx="2"/>
            </svg>
            <h1 style="color: white; margin: 10px 0; font-size: 24px; font-weight: 700;">{title}</h1>
            <p style="color: #94a3b8; margin: 5px 0; font-size: 14px;">{subtitle}</p>
        </div>
        """

    def _get_footer_html(self) -> str:
        """Reusable footer"""
        return f"""
        <div style="background: #f8fafc; padding: 25px 30px; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 13px; text-align: center;">
                NSE Sentiment Analysis Stock Market System
            </p>
            <p style="margin: 0; color: #94a3b8; font-size: 12px; text-align: center;">
                © {datetime.now().year} All rights reserved.
            </p>
        </div>
        """

    def _create_analytics_template(self, data: Dict) -> str:
        """Create daily analytics email with dashboard theme"""
        top_performers = data.get('top_performers', [])
        predictions = data.get('predictions', [])
        sentiment = data.get('sentiment', {})
        market_status = data.get('market_status', 'Closed')
        
        # Build performers HTML
        performers_html = ""
        for stock in top_performers[:5]:
            change_icon = "↑" if stock['change'] >= 0 else "↓"
            change_color = "#10b981" if stock['change'] >= 0 else "#ef4444"
            performers_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                    <strong>{stock['symbol']}</strong><br>
                    <span style="color: #64748b; font-size: 12px;">{stock['name']}</span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: right;">
                    KES {stock['price']:.2f}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: right;">
                    <span style="color: {change_color}; font-weight: 600;">
                        {change_icon} {abs(stock['change']):.2f}%
                    </span>
                </td>
            </tr>
            """
        
        # Build predictions HTML
        predictions_html = ""
        for pred in predictions[:3]:
            trend_color = "#10b981" if pred['trend'] == 'up' else "#ef4444"
            trend_icon = "↑" if pred['trend'] == 'up' else "↓"
            predictions_html += f"""
            <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid {trend_color};">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <strong>{pred['symbol']}</strong>
                        <p style="margin: 5px 0; color: #64748b; font-size: 13px;">Target: {pred['target_date']}</p>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 18px; font-weight: 700; color: {trend_color};">
                            {trend_icon} KES {pred['predicted_price']:.2f}
                        </div>
                        <div style="font-size: 12px; color: #64748b;">Confidence: {pred['confidence']}%</div>
                    </div>
                </div>
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Daily Analytics</title></head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background: #f1f5f9;">
    <div style="max-width: 650px; margin: 0 auto; background: white;">
        {self._get_header_html("NSE Market Analytics", f"Daily Report - {date.today().strftime('%B %d, %Y')}")}
        
        <div style="padding: 30px;">
            <div style="margin-bottom: 30px;">
                <h2 style="color: #0f172a; font-size: 20px; margin: 0 0 20px 0; border-bottom: 3px solid #10b981; padding-bottom: 10px;">
                    📈 Top Performers
                </h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8fafc;">
                            <th style="padding: 12px; text-align: left; color: #64748b; font-size: 12px;">STOCK</th>
                            <th style="padding: 12px; text-align: right; color: #64748b; font-size: 12px;">PRICE</th>
                            <th style="padding: 12px; text-align: right; color: #64748b; font-size: 12px;">CHANGE</th>
                        </tr>
                    </thead>
                    <tbody>{performers_html}</tbody>
                </table>
            </div>
            
            <div style="margin-bottom: 30px;">
                <h2 style="color: #0f172a; font-size: 20px; margin: 0 0 20px 0; border-bottom: 3px solid #10b981; padding-bottom: 10px;">
                    🎯 AI Predictions
                </h2>
                {predictions_html}
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:3000/pages/dashboard.html" style="display: inline-block; background: #10b981; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                    View Full Dashboard →
                </a>
            </div>
        </div>
        
        {self._get_footer_html()}
    </div>
</body>
</html>
        """

    def _create_alert_template(self, symbol: str, alert_type: str, message: str, 
                               current_price: float, predicted_price: Optional[float]) -> str:
        """Create stock alert email"""
        alert_colors = {
            'Price Target': '#10b981',
            'Volatility Alert': '#f59e0b',
            'Prediction Alert': '#3b82f6'
        }
        alert_color = alert_colors.get(alert_type, '#10b981')
        
        prediction_section = ""
        if predicted_price:
            change_pct = ((predicted_price - current_price) / current_price) * 100
            prediction_section = f"""
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin: 0 0 15px 0;">Price Prediction</h3>
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <div style="font-size: 13px; color: #64748b;">Current</div>
                        <div style="font-size: 24px; font-weight: 700;">KES {current_price:.2f}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 13px; color: #64748b;">Predicted</div>
                        <div style="font-size: 24px; font-weight: 700; color: {alert_color};">KES {predicted_price:.2f}</div>
                        <div style="color: {'#10b981' if change_pct > 0 else '#ef4444'};">
                            {'↑' if change_pct > 0 else '↓'} {abs(change_pct):.2f}%
                        </div>
                    </div>
                </div>
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Stock Alert</title></head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background: #f1f5f9;">
    <div style="max-width: 600px; margin: 0 auto; background: white;">
        {self._get_header_html("🔔 Stock Alert", symbol)}
        
        <div style="padding: 30px;">
            <div style="background: {alert_color}; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="margin: 0; font-size: 18px;">{alert_type}</h2>
            </div>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6;">{message}</p>
            
            {prediction_section}
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:3000/pages/stocks.html" style="display: inline-block; background: #10b981; color: white; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                    View Details →
                </a>
            </div>
        </div>
        
        {self._get_footer_html()}
    </div>
</body>
</html>
        """

    def _create_news_template(self, news_articles: List[Dict]) -> str:
        """Create news digest email"""
        news_html = ""
        for article in news_articles[:10]:
            sentiment_color = {
                'positive': '#10b981',
                'neutral': '#64748b',
                'negative': '#ef4444'
            }.get(article.get('sentiment', 'neutral'), '#64748b')
            
            news_html += f"""
            <div style="border-left: 3px solid {sentiment_color}; padding: 15px; background: #f8fafc; margin-bottom: 15px; border-radius: 0 8px 8px 0;">
                <h3 style="margin: 0 0 10px 0; color: #0f172a; font-size: 16px;">{article['title']}</h3>
                <p style="margin: 0 0 10px 0; color: #64748b; font-size: 14px;">{article.get('summary', '')[:150]}...</p>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94a3b8; font-size: 12px;">{article.get('source', 'News')}</span>
                    <span style="background: {sentiment_color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px;">
                        {article.get('sentiment', 'Neutral').title()}
                    </span>
                </div>
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>News Digest</title></head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background: #f1f5f9;">
    <div style="max-width: 650px; margin: 0 auto; background: white;">
        {self._get_header_html("📰 Market News Digest")}
        
        <div style="padding: 30px;">
            <p style="color: #64748b; margin: 0 0 25px 0;">Latest NSE market news and analysis:</p>
            {news_html}
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:3000/pages/sentiment.html" style="display: inline-block; background: #10b981; color: white; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                    View All News →
                </a>
            </div>
        </div>
        
        {self._get_footer_html()}
    </div>
</body>
</html>
        """


# Global instance
stock_email_service = StockEmailService()
