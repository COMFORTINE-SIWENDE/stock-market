import math
from datetime import date, timedelta

import click

from app.utils.logger import logger


@click.group()
def cli():
    """Stock Sentiment Predictor — CLI"""
    pass


@cli.command()
def run():
    """Start interactive agent session."""
    from app.agent.agent import Agent
    from app.config.database import get_sync_session
    from app.services.scheduler import start_scheduler, stop_scheduler

    start_scheduler(get_sync_session)
    agent = Agent()
    click.echo("Stock Sentiment Predictor — type 'exit' to quit\n")
    try:
        while True:
            query = input("You: ").strip()
            if query.lower() in ("exit", "quit", "q"):
                break
            if not query:
                continue
            with get_sync_session() as session:
                response = agent.run(query, session)
            click.echo(f"Agent: {response}\n")
    except KeyboardInterrupt:
        click.echo("\nGoodbye!")
    finally:
        stop_scheduler()


@cli.command("train-model")
@click.option("--symbol", required=True, help="Stock ticker symbol (e.g. AAPL)")
def train_model(symbol: str):
    """Train LSTM model for a symbol."""
    from app.services.prediction_service import train_model as _train
    from app.config.database import get_sync_session

    click.echo(f"Training model for {symbol.upper()}...")
    with get_sync_session() as session:
        metrics = _train(session, symbol.upper())
    click.echo(f"Done. MSE={metrics['mse']:.6f}  MAE={metrics['mae']:.6f}")


@cli.command("collect-data")
@click.option("--symbols", "-s", multiple=True, required=True, help="Stock ticker symbols")
@click.option("--days", default=365, show_default=True, help="Days of history to fetch")
def collect_data(symbols: tuple, days: int):
    """Collect stock data and news for given symbols."""
    from app.services.data_service import collect_stock_data, collect_news
    from app.config.database import get_sync_session

    end = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()

    for symbol in symbols:
        symbol = symbol.upper()
        with get_sync_session() as session:
            stock_count = collect_stock_data(session, symbol, start, end)
            news_count = collect_news(session, symbol)
        click.echo(f"{symbol}: {stock_count} stock records, {news_count} news articles inserted")


@cli.command()
@click.option("--symbol", required=True, help="Stock ticker symbol")
@click.option("--days", default=1, show_default=True, help="Number of days to predict")
def predict(symbol: str, days: int):
    """Generate price predictions for a symbol."""
    from app.services.prediction_service import generate_prediction
    from app.config.database import get_sync_session

    symbol = symbol.upper()
    with get_sync_session() as session:
        preds = generate_prediction(session, symbol, days)

    if not preds:
        click.echo(f"No predictions generated for {symbol}. Ensure data is collected first.")
        return

    click.echo(f"\nPredictions for {symbol}:")
    for p in preds:
        click.echo(
            f"  {p.target_date}  ${p.predicted_price:.2f}  "
            f"trend={p.trend_direction}  confidence={p.confidence_score:.0%}  [{p.model_source}]"
        )


@cli.command("analyze-sentiment")
@click.option("--symbol", required=True, help="Stock ticker symbol")
def analyze_sentiment(symbol: str):
    """Analyze sentiment for recent articles of a symbol."""
    from app.services.sentiment_service import analyze_pending_articles, aggregate_daily_sentiment
    from app.config.database import get_sync_session

    symbol = symbol.upper()
    with get_sync_session() as session:
        count = analyze_pending_articles(session, symbol)
        daily = aggregate_daily_sentiment(session, symbol, date.today().isoformat())

    click.echo(f"Analyzed {count} new articles for {symbol}")
    if daily:
        click.echo(
            f"Daily sentiment ({daily.date}): score={daily.avg_sentiment_score:.3f}  "
            f"articles={daily.article_count}  "
            f"+{daily.positive_count} ={daily.neutral_count} -{daily.negative_count}"
        )
    else:
        click.echo("No daily sentiment data available.")


@cli.command()
@click.option("--symbol", required=True, help="Stock ticker symbol")
def backtest(symbol: str):
    """Backtest prediction accuracy for a symbol."""
    from app.models.prediction import Prediction
    from app.models.stock import StockSymbol
    from app.config.database import get_sync_session
    from sqlmodel import select

    symbol = symbol.upper()
    with get_sync_session() as session:
        stock_symbol = session.exec(
            select(StockSymbol).where(StockSymbol.symbol == symbol)
        ).first()
        if not stock_symbol:
            click.echo(f"Symbol {symbol} not found in database.")
            return
        preds = session.exec(
            select(Prediction).where(
                Prediction.symbol_id == stock_symbol.id,
                Prediction.actual_price.is_not(None),
            )
        ).all()

    if not preds:
        click.echo(f"No backtestable predictions found for {symbol} (need actual_price populated).")
        return

    errors = [abs(p.predicted_price - p.actual_price) for p in preds]
    mae = sum(errors) / len(errors)
    rmse = math.sqrt(sum(e ** 2 for e in errors) / len(errors))
    click.echo(f"\nBacktest results for {symbol} ({len(preds)} predictions):")
    click.echo(f"  MAE:  ${mae:.4f}")
    click.echo(f"  RMSE: ${rmse:.4f}")


if __name__ == "__main__":
    cli()
