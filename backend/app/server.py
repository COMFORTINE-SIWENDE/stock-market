"""
Lightweight aiohttp HTTP server exposing the backend as JSON REST endpoints.
Run with: python -m app.server
"""
import json
from datetime import date, timedelta

from aiohttp import web

from app.config.database import get_sync_session
from app.utils.logger import logger


# ── helpers ──────────────────────────────────────────────────────────────────

def _json(data, status=200):
    return web.Response(
        text=json.dumps(data, default=str),
        content_type="application/json",
        status=status,
    )


def _err(msg, status=400):
    return _json({"error": msg}, status)


def _cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        return _cors(web.Response(status=204))
    response = await handler(request)
    return _cors(response)


# ── auth ─────────────────────────────────────────────────────────────────────

async def register(request):
    try:
        body = await request.json()
        from app.services.auth_service import register_user
        with get_sync_session() as session:
            user = register_user(
                session,
                email=body["email"],
                username=body["username"],
                password=body["password"],
                full_name=body.get("full_name"),
            )
        return _json({"id": user.id, "username": user.username, "email": user.email})
    except ValueError as e:
        return _err(str(e))
    except Exception as e:
        logger.error(f"register error: {e}")
        return _err(str(e), 500)


async def login(request):
    try:
        body = await request.json()
        from app.services.auth_service import login_user
        with get_sync_session() as session:
            token, sess = login_user(
                session,
                username_or_email=body["username_or_email"],
                password=body["password"],
                ip=request.remote,
                user_agent=request.headers.get("User-Agent"),
            )
        return _json({"token": token, "session_id": sess.id, "expires_at": str(sess.expires_at)})
    except (ValueError, PermissionError) as e:
        return _err(str(e), 401)
    except Exception as e:
        logger.error(f"login error: {e}")
        return _err(str(e), 500)


async def logout(request):
    try:
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token:
            return _err("Authorization header required", 401)
        from app.services.auth_service import logout_user
        with get_sync_session() as session:
            logout_user(session, token)
        return _json({"message": "Logged out"})
    except Exception as e:
        return _err(str(e), 500)


# ── stocks ───────────────────────────────────────────────────────────────────

async def stock_data(request):
    symbol = request.match_info["symbol"].upper()
    start = request.rel_url.query.get("start", (date.today() - timedelta(days=365)).isoformat())
    end = request.rel_url.query.get("end", date.today().isoformat())
    from app.tools.data_tools import fetch_historical_data
    data = fetch_historical_data(symbol, start, end)
    return _json({"symbol": symbol, "data": data})


async def stock_price(request):
    symbol = request.match_info["symbol"].upper()
    from app.tools.data_tools import fetch_current_price
    price = fetch_current_price(symbol)
    return _json({"symbol": symbol, "price": price})


async def stock_indicators(request):
    symbol = request.match_info["symbol"].upper()
    start = request.rel_url.query.get("start", (date.today() - timedelta(days=60)).isoformat())
    end = request.rel_url.query.get("end", date.today().isoformat())
    from app.tools.data_tools import get_technical_indicators
    indicators = get_technical_indicators(symbol, (start, end))
    return _json({"symbol": symbol, "indicators": indicators})


async def collect_data(request):
    try:
        body = await request.json()
        symbols = body.get("symbols", [])
        days = int(body.get("days", 365))
        if not symbols:
            return _err("symbols list required")
        from app.services.data_service import collect_stock_data, collect_news
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=days)).isoformat()
        results = {}
        for symbol in symbols:
            symbol = symbol.upper()
            with get_sync_session() as session:
                stock_count = collect_stock_data(session, symbol, start, end)
                news_count = collect_news(session, symbol)
            results[symbol] = {"stock_records": stock_count, "news_articles": news_count}
        return _json(results)
    except Exception as e:
        logger.error(f"collect_data error: {e}")
        return _err(str(e), 500)


# ── sentiment ─────────────────────────────────────────────────────────────────

async def get_sentiment(request):
    symbol = request.match_info["symbol"].upper()
    target_date = request.rel_url.query.get("date", date.today().isoformat())
    start = request.rel_url.query.get("start", (date.today() - timedelta(days=30)).isoformat())
    end = request.rel_url.query.get("end", date.today().isoformat())
    from app.tools.sentiment_tools import get_daily_sentiment
    with get_sync_session() as session:
        data = get_daily_sentiment(symbol, (start, end), session)
    return _json({"symbol": symbol, "sentiment": data})


async def analyze_sentiment(request):
    symbol = request.match_info["symbol"].upper()
    try:
        from app.services.sentiment_service import analyze_pending_articles, aggregate_daily_sentiment
        with get_sync_session() as session:
            count = analyze_pending_articles(session, symbol)
            daily = aggregate_daily_sentiment(session, symbol, date.today().isoformat())
        result = {"articles_analyzed": count, "daily_sentiment": None}
        if daily:
            result["daily_sentiment"] = {
                "date": str(daily.date),
                "avg_sentiment_score": daily.avg_sentiment_score,
                "article_count": daily.article_count,
                "positive_count": daily.positive_count,
                "neutral_count": daily.neutral_count,
                "negative_count": daily.negative_count,
            }
        return _json(result)
    except Exception as e:
        logger.error(f"analyze_sentiment error: {e}")
        return _err(str(e), 500)


# ── predictions ───────────────────────────────────────────────────────────────

async def get_predictions(request):
    symbol = request.match_info["symbol"].upper()
    days = int(request.rel_url.query.get("days", 1))
    try:
        from app.services.prediction_service import generate_prediction
        with get_sync_session() as session:
            preds = generate_prediction(session, symbol, days)
        return _json({
            "symbol": symbol,
            "predictions": [
                {
                    "target_date": str(p.target_date),
                    "predicted_price": p.predicted_price,
                    "confidence_score": p.confidence_score,
                    "trend_direction": p.trend_direction,
                    "model_source": p.model_source,
                }
                for p in preds
            ],
        })
    except Exception as e:
        logger.error(f"get_predictions error: {e}")
        return _err(str(e), 500)


async def train_model(request):
    symbol = request.match_info["symbol"].upper()
    try:
        from app.services.prediction_service import train_model as _train
        with get_sync_session() as session:
            metrics = _train(session, symbol)
        return _json({"symbol": symbol, "mse": metrics["mse"], "mae": metrics["mae"]})
    except Exception as e:
        logger.error(f"train_model error: {e}")
        return _err(str(e), 500)


async def prediction_history(request):
    symbol = request.match_info["symbol"].upper()
    from app.tools.prediction_tools import get_prediction_history
    with get_sync_session() as session:
        history = get_prediction_history(symbol, session)
    return _json({"symbol": symbol, "history": history})


async def backtest(request):
    symbol = request.match_info["symbol"].upper()
    import math
    from app.models.prediction import Prediction
    from app.models.stock import StockSymbol
    from sqlmodel import select
    with get_sync_session() as session:
        stock_symbol = session.exec(select(StockSymbol).where(StockSymbol.symbol == symbol)).first()
        if not stock_symbol:
            return _err(f"Symbol {symbol} not found", 404)
        preds = session.exec(
            select(Prediction).where(
                Prediction.symbol_id == stock_symbol.id,
                Prediction.actual_price.is_not(None),
            )
        ).all()
    if not preds:
        return _json({"symbol": symbol, "message": "No backtestable predictions found", "count": 0})
    errors = [abs(p.predicted_price - p.actual_price) for p in preds]
    mae = sum(errors) / len(errors)
    rmse = math.sqrt(sum(e ** 2 for e in errors) / len(errors))
    return _json({"symbol": symbol, "count": len(preds), "mae": round(mae, 4), "rmse": round(rmse, 4)})


# ── agent ─────────────────────────────────────────────────────────────────────

async def agent_query(request):
    try:
        body = await request.json()
        query = body.get("query", "").strip()
        if not query:
            return _err("query field required")
        from app.agent.agent import Agent
        agent = Agent()
        with get_sync_session() as session:
            response = agent.run(query, session)
        return _json({"query": query, "response": response})
    except Exception as e:
        logger.error(f"agent_query error: {e}")
        return _err(str(e), 500)


# ── symbols ───────────────────────────────────────────────────────────────────

async def search_symbols(request):
    q = request.rel_url.query.get("q", "").strip()
    if not q:
        return _err("q parameter required")
    from app.tools.utility_tools import search_symbols as _search
    with get_sync_session() as session:
        results = _search(q, session)
    return _json({"results": results})


# ── app factory ───────────────────────────────────────────────────────────────

def create_app():
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_post("/auth/register", register)
    app.router.add_post("/auth/login", login)
    app.router.add_post("/auth/logout", logout)
    app.router.add_get("/stocks/{symbol}/data", stock_data)
    app.router.add_get("/stocks/{symbol}/price", stock_price)
    app.router.add_get("/stocks/{symbol}/indicators", stock_indicators)
    app.router.add_post("/stocks/collect", collect_data)
    app.router.add_get("/sentiment/{symbol}", get_sentiment)
    app.router.add_post("/sentiment/{symbol}/analyze", analyze_sentiment)
    app.router.add_get("/predictions/{symbol}", get_predictions)
    app.router.add_post("/predictions/{symbol}/train", train_model)
    app.router.add_get("/predictions/{symbol}/history", prediction_history)
    app.router.add_get("/predictions/{symbol}/backtest", backtest)
    app.router.add_post("/agent/query", agent_query)
    app.router.add_get("/symbols/search", search_symbols)
    return app


if __name__ == "__main__":
    from app.config.config import settings
    app = create_app()
    logger.info(f"Starting server on http://0.0.0.0:8000")
    web.run_app(app, host="0.0.0.0", port=8000)
