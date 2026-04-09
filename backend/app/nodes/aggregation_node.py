from app.nodes.base_node import BaseNode


class AggregationNode(BaseNode):
    def _run(self, inputs: dict) -> dict:
        summary = {
            "symbol": inputs.get("symbol"),
            "stock_records_collected": inputs.get("stock_count", 0),
            "news_articles_collected": inputs.get("news_count", 0),
            "articles_analyzed": inputs.get("articles_analyzed", 0),
            "daily_sentiment": inputs.get("daily_sentiment"),
            "predictions": inputs.get("predictions", []),
        }
        return {**inputs, "summary": summary}
