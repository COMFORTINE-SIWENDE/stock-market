from datetime import date
from app.nodes.base_node import BaseNode
from app.services.sentiment_service import analyze_pending_articles, aggregate_daily_sentiment


class AnalysisNode(BaseNode):
    def __init__(self, session):
        self.session = session

    def _run(self, inputs: dict) -> dict:
        symbol = inputs["symbol"]
        date_str = inputs.get("end_date", date.today().isoformat())
        count = analyze_pending_articles(self.session, symbol)
        daily = aggregate_daily_sentiment(self.session, symbol, date_str)
        return {
            **inputs,
            "articles_analyzed": count,
            "daily_sentiment": {
                "date": str(daily.date),
                "avg_score": daily.avg_sentiment_score,
                "article_count": daily.article_count,
            } if daily else None,
        }
