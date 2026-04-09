import json
from app.nodes.base_node import BaseNode


class OutputNode(BaseNode):
    def _run(self, inputs: dict) -> dict:
        summary = inputs.get("summary", inputs)
        output_lines = [f"=== Results for {summary.get('symbol', 'N/A')} ==="]
        if summary.get("daily_sentiment"):
            ds = summary["daily_sentiment"]
            output_lines.append(
                f"Sentiment ({ds.get('date')}): {ds.get('avg_score', 0):.3f} "
                f"({ds.get('article_count', 0)} articles)"
            )
        for pred in summary.get("predictions", []):
            output_lines.append(
                f"  {pred['target_date']}: ${pred['predicted_price']:.2f} "
                f"({pred['trend_direction']}) confidence={pred['confidence_score']:.2f} "
                f"[{pred['model_source']}]"
            )
        formatted = "\n".join(output_lines)
        return {**inputs, "output": formatted}
