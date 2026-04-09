from app.nodes.base_node import BaseNode
from app.tools.prediction_tools import engineer_features


class PreprocessingNode(BaseNode):
    def __init__(self, session):
        self.session = session

    def _run(self, inputs: dict) -> dict:
        symbol = inputs["symbol"]
        end_date = inputs.get("end_date")
        from datetime import date
        if not end_date:
            end_date = date.today().isoformat()
        df = engineer_features(self.session, symbol, end_date)
        return {**inputs, "features": df.to_dict(orient="records") if not df.empty else []}
