from app.nodes.base_node import BaseNode
from app.services.prediction_service import generate_prediction


class PredictionNode(BaseNode):
    def __init__(self, session):
        self.session = session

    def _run(self, inputs: dict) -> dict:
        symbol = inputs["symbol"]
        horizon_days = inputs.get("horizon_days", 1)
        user_id = inputs.get("user_id")
        predictions = generate_prediction(self.session, symbol, horizon_days, user_id)
        return {
            **inputs,
            "predictions": [
                {
                    "target_date": str(p.target_date),
                    "predicted_price": p.predicted_price,
                    "confidence_score": p.confidence_score,
                    "trend_direction": p.trend_direction,
                    "model_source": p.model_source,
                }
                for p in predictions
            ],
        }
