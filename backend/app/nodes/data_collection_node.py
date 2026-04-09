from app.nodes.base_node import BaseNode
from app.services.data_service import collect_stock_data, collect_news


class DataCollectionNode(BaseNode):
    def __init__(self, session):
        self.session = session

    def _run(self, inputs: dict) -> dict:
        symbol = inputs["symbol"]
        start_date = inputs.get("start_date", "2020-01-01")
        end_date = inputs.get("end_date")
        from datetime import date
        if not end_date:
            end_date = date.today().isoformat()
        stock_count = collect_stock_data(self.session, symbol, start_date, end_date)
        news_count = collect_news(self.session, symbol)
        return {**inputs, "stock_count": stock_count, "news_count": news_count}
