import json
from openai import AzureOpenAI
from sqlmodel import Session

from app.config.config import settings
from app.utils.logger import logger

SYSTEM_PROMPT = """You are a financial analyst assistant with access to stock market data,
sentiment analysis, and price prediction tools.

When the user asks a question, respond with a JSON object in this exact format:
{
  "intent_type": "<one of: get_prediction, analyze_sentiment, view_stock_data, compare_stocks, explain_trends, general_question>",
  "entities": {
    "symbol": "<stock ticker symbol if mentioned, else null>",
    "symbols": ["<list of symbols if multiple mentioned>"],
    "horizon_days": <number of days for prediction, default 1>,
    "date_range": ["<start_date YYYY-MM-DD>", "<end_date YYYY-MM-DD>"]
  },
  "response": "<natural language response to the user>"
}

Always respond with valid JSON only. No markdown, no extra text."""


class Agent:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT

    def classify_intent(self, query: str) -> dict:
        """Send query to GPT-Nano and parse intent JSON."""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                max_completion_tokens=512,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"GPT returned non-JSON response: {e}")
            return {"intent_type": "general_question", "entities": {}, "response": "Could you clarify your question?"}
        except Exception as e:
            logger.error(f"classify_intent failed: {e}")
            return {"intent_type": "general_question", "entities": {}, "response": "I encountered an error. Please try again."}

    def run(self, query: str, session: Session) -> str:
        """Classify intent, execute tools, return natural language response."""
        intent_data = self.classify_intent(query)
        intent_type = intent_data.get("intent_type", "general_question")
        entities = intent_data.get("entities", {})
        base_response = intent_data.get("response", "")
        symbol = entities.get("symbol")
        horizon_days = entities.get("horizon_days", 1) or 1

        try:
            if intent_type == "get_prediction" and symbol:
                from app.services.prediction_service import generate_prediction
                preds = generate_prediction(session, symbol, horizon_days)
                if preds:
                    lines = [f"Price predictions for {symbol}:"]
                    for p in preds:
                        lines.append(
                            f"  {p.target_date}: ${p.predicted_price:.2f} "
                            f"({p.trend_direction}) confidence={p.confidence_score:.0%} [{p.model_source}]"
                        )
                    return "\n".join(lines)

            elif intent_type == "analyze_sentiment" and symbol:
                from app.services.sentiment_service import analyze_pending_articles, aggregate_daily_sentiment
                from datetime import date
                count = analyze_pending_articles(session, symbol)
                daily = aggregate_daily_sentiment(session, symbol, date.today().isoformat())
                if daily:
                    return (
                        f"Sentiment for {symbol} on {daily.date}: score={daily.avg_sentiment_score:.3f}, "
                        f"{daily.article_count} articles (+{daily.positive_count} ={daily.neutral_count} -{daily.negative_count})"
                    )
                return f"Analyzed {count} articles for {symbol}. No daily sentiment data yet."

            elif intent_type == "view_stock_data" and symbol:
                from app.tools.data_tools import fetch_current_price
                price = fetch_current_price(symbol)
                return f"Current price for {symbol}: ${price:.2f}"

            elif intent_type == "compare_stocks":
                symbols = entities.get("symbols", [])
                if symbols:
                    from app.tools.data_tools import fetch_current_price
                    lines = ["Stock comparison:"]
                    for sym in symbols:
                        price = fetch_current_price(sym)
                        lines.append(f"  {sym}: ${price:.2f}")
                    return "\n".join(lines)

        except Exception as e:
            logger.error(f"Agent tool execution failed for intent={intent_type}: {e}")
            return f"I encountered an error while processing your request: {e}"

        return base_response or "I'm not sure how to help with that. Try asking about a specific stock symbol."
