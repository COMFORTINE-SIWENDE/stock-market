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


async def get_current_user(request):
    try:
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token:
            return _err("Authorization header required", 401)
        from app.services.auth_service import verify_token
        with get_sync_session() as session:
            user = verify_token(session, token)
        return _json({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": str(user.created_at),
        })
    except PermissionError as e:
        return _err(str(e), 401)
    except Exception as e:
        logger.error(f"get_current_user error: {e}")
        return _err(str(e), 500)


# ── stocks ───────────────────────────────────────────────────────────────────

async def stock_data(request):
    symbol = request.match_info["symbol"].upper()
    start = request.rel_url.query.get("start", (date.today() - timedelta(days=365)).isoformat())
    end = request.rel_url.query.get("end", date.today().isoformat())
    
    # Fetch from database instead of Yahoo Finance
    from app.models.stock import StockData, StockSymbol
    from sqlmodel import select
    
    with get_sync_session() as session:
        # Get stock symbol
        stock_symbol = session.exec(
            select(StockSymbol).where(StockSymbol.symbol == symbol)
        ).first()
        
        if not stock_symbol:
            return _json({"symbol": symbol, "data": []})
        
        # Get stock data
        stock_data_records = session.exec(
            select(StockData)
            .where(StockData.symbol_id == stock_symbol.id)
            .where(StockData.date >= start)
            .where(StockData.date <= end)
            .order_by(StockData.date)
        ).all()
        
        data = [
            {
                "date": str(rec.date),
                "open": rec.open,
                "high": rec.high,
                "low": rec.low,
                "close": rec.close,
                "volume": rec.volume,
                "adj_close": rec.adj_close or rec.close
            }
            for rec in stock_data_records
        ]
    
    return _json({"symbol": symbol, "data": data})


async def stock_price(request):
    symbol = request.match_info["symbol"].upper()
    
    # Fetch latest price from database
    from app.models.stock import StockData, StockSymbol
    from sqlmodel import select
    
    with get_sync_session() as session:
        # Get stock symbol
        stock_symbol = session.exec(
            select(StockSymbol).where(StockSymbol.symbol == symbol)
        ).first()
        
        if not stock_symbol:
            return _json({"symbol": symbol, "price": 0.0})
        
        # Get latest stock data
        latest = session.exec(
            select(StockData)
            .where(StockData.symbol_id == stock_symbol.id)
            .order_by(StockData.date.desc())
            .limit(1)
        ).first()
        
        price = latest.close if latest else 0.0
    
    return _json({"symbol": symbol, "price": price})


async def stock_indicators(request):
    symbol = request.match_info["symbol"].upper()
    start = request.rel_url.query.get("start", (date.today() - timedelta(days=60)).isoformat())
    end = request.rel_url.query.get("end", date.today().isoformat())
    
    # Calculate indicators from database data
    from app.models.stock import StockData, StockSymbol
    from sqlmodel import select
    
    with get_sync_session() as session:
        # Get stock symbol
        stock_symbol = session.exec(
            select(StockSymbol).where(StockSymbol.symbol == symbol)
        ).first()
        
        if not stock_symbol:
            return _json({"symbol": symbol, "indicators": {}})
        
        # Get stock data for calculation
        stock_data_records = session.exec(
            select(StockData)
            .where(StockData.symbol_id == stock_symbol.id)
            .where(StockData.date >= start)
            .where(StockData.date <= end)
            .order_by(StockData.date)
        ).all()
        
        if not stock_data_records:
            return _json({"symbol": symbol, "indicators": {}})
        
        closes = [rec.close for rec in stock_data_records]
        
        # Calculate SMA 5
        sma5 = sum(closes[-5:]) / min(5, len(closes)) if len(closes) >= 5 else None
        
        # Calculate SMA 20
        sma20 = sum(closes[-20:]) / min(20, len(closes)) if len(closes) >= 20 else None
        
        # Calculate RSI (14 period)
        rsi = None
        if len(closes) >= 15:
            # Calculate price changes
            changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            recent_changes = changes[-14:]
            
            gains = [c if c > 0 else 0 for c in recent_changes]
            losses = [-c if c < 0 else 0 for c in recent_changes]
            
            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14
            
            if avg_loss != 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 100
        
        # Calculate volatility
        volatility = None
        if len(closes) >= 2:
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            recent = returns[-20:] if len(returns) >= 20 else returns
            mean_r = sum(recent) / len(recent)
            variance = sum((r - mean_r) ** 2 for r in recent) / len(recent)
            volatility = (variance ** 0.5) * 100  # Convert to percentage
        
        indicators = {
            "sma_5": sma5,
            "sma_20": sma20,
            "rsi": rsi,
            "volatility": volatility
        }
    
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
    """Get price predictions using trained LSTM models"""
    symbol = request.match_info["symbol"].upper()
    days = int(request.rel_url.query.get("days", 7))
    send_email = request.rel_url.query.get("send_email", "false").lower() == "true"
    
    # Ensure .NR suffix for NSE stocks
    if not symbol.endswith('.NR'):
        symbol = f"{symbol}.NR"
    
    try:
        from app.services.prediction_service import get_prediction_service
        
        prediction_service = get_prediction_service()
        
        with get_sync_session() as session:
            # Get user_id and email from token if available
            user_id = None
            user_email = None
            token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            if token:
                try:
                    from app.services.auth_service import verify_token
                    user = verify_token(session, token)
                    user_id = user.id
                    user_email = user.email
                except:
                    pass
            
            # Generate prediction
            if days == 1:
                pred = prediction_service.predict_next_day(session, symbol, user_id)
                if not pred:
                    return _err(f"Failed to generate prediction for {symbol}. Model may not be available.", 500)
                
                predictions = [pred]
            else:
                predictions = prediction_service.predict_multiple_days(session, symbol, days, user_id)
                if not predictions:
                    return _err(f"Failed to generate predictions for {symbol}", 500)
        
        response_data = {
            "symbol": symbol,
            "predictions": [
                {
                    "target_date": str(p['target_date']),
                    "predicted_price": round(p['predicted_price'], 2),
                    "current_price": round(p['current_price'], 2),
                    "price_change": round(p['price_change'], 2),
                    "price_change_pct": round(p['price_change_pct'], 2),
                    "confidence_score": round(p['confidence_score'], 4),
                    "trend_direction": p['trend_direction'],
                    "model_source": p['model_source'],
                    "model_mape": round(p['model_mape'], 2),
                    "prediction_id": p.get('prediction_id')
                }
                for p in predictions
            ],
            "last_data_date": str(predictions[0]['last_data_date']) if predictions else None
        }
        
        # Send email if requested
        if send_email and user_email:
            try:
                from app.services.stock_email_service import stock_email_service
                
                # Prepare prediction data for email
                pred = predictions[0]
                stock_email_service.send_stock_alert_email(
                    to_email=user_email,
                    symbol=symbol,
                    alert_type="Prediction Alert",
                    message=f"Our AI model predicts {symbol} will reach KES {pred['predicted_price']:.2f} on {pred['target_date']} with {int(pred['confidence_score'] * 100)}% confidence.",
                    current_price=pred['current_price'],
                    predicted_price=pred['predicted_price']
                )
                response_data['email_sent'] = True
                logger.info(f"Prediction email sent to {user_email} for {symbol}")
            except Exception as e:
                logger.error(f"Failed to send prediction email: {e}")
                response_data['email_sent'] = False
        
        return _json(response_data)
    except Exception as e:
        logger.error(f"get_predictions error: {e}")
        import traceback
        traceback.print_exc()
        return _err(str(e), 500)


async def train_model(request):
    """Train or retrain LSTM model for a stock (admin only)"""
    symbol = request.match_info["symbol"].upper()
    
    # Ensure .NR suffix
    if not symbol.endswith('.NR'):
        symbol = f"{symbol}.NR"
    
    try:
        body = await request.json()
        epochs = body.get("epochs", 50)
        batch_size = body.get("batch_size", 32)
        
        return _json({
            "message": "Model training not implemented in API. Use nse_lstm_trainer.py script",
            "symbol": symbol,
            "note": "Training requires significant compute resources and should be run offline"
        })
    except Exception as e:
        logger.error(f"train_model error: {e}")
        return _err(str(e), 500)


async def prediction_history(request):
    """Get prediction history for a stock"""
    symbol = request.match_info["symbol"].upper()
    limit = int(request.rel_url.query.get("limit", 30))
    
    # Ensure .NR suffix
    if not symbol.endswith('.NR'):
        symbol = f"{symbol}.NR"
    
    try:
        from app.models.prediction import Prediction
        from app.models.stock import StockSymbol
        from sqlmodel import select
        
        with get_sync_session() as session:
            # Get stock symbol
            stock_symbol = session.exec(
                select(StockSymbol).where(StockSymbol.symbol == symbol)
            ).first()
            
            if not stock_symbol:
                return _json({"symbol": symbol, "history": []})
            
            # Get predictions
            predictions = session.exec(
                select(Prediction)
                .where(Prediction.symbol_id == stock_symbol.id)
                .order_by(Prediction.created_at.desc())
                .limit(limit)
            ).all()
            
            history = []
            for p in predictions:
                # Calculate accuracy if actual price is available
                accuracy = None
                error_pct = None
                if p.actual_price:
                    error = abs(p.predicted_price - p.actual_price)
                    error_pct = (error / p.actual_price) * 100
                    accuracy = max(0, 100 - error_pct)
                
                history.append({
                    "id": p.id,
                    "prediction_date": str(p.prediction_date),
                    "target_date": str(p.target_date),
                    "predicted_price": round(p.predicted_price, 2),
                    "actual_price": round(p.actual_price, 2) if p.actual_price else None,
                    "confidence_score": round(p.confidence_score, 4),
                    "trend_direction": p.trend_direction,
                    "model_source": p.model_source,
                    "accuracy_pct": round(accuracy, 2) if accuracy else None,
                    "error_pct": round(error_pct, 2) if error_pct else None,
                    "created_at": str(p.created_at)
                })
        
        return _json({"symbol": symbol, "history": history, "total": len(history)})
    except Exception as e:
        logger.error(f"prediction_history error: {e}")
        return _err(str(e), 500)


async def available_models(request):
    """Get list of available trained models"""
    try:
        from app.services.prediction_service import get_prediction_service
        
        prediction_service = get_prediction_service()
        models = prediction_service.get_available_models()
        
        return _json({
            "models": models,
            "total": len(models)
        })
    except Exception as e:
        logger.error(f"available_models error: {e}")
        return _err(str(e), 500)


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


# ── NSE market ────────────────────────────────────────────────────────────────

async def nse_market_status(request):
    try:
        from app.services.trading_hours_validator import TradingHoursValidator
        from app.services.timezone_handler import TimezoneHandler
        from pathlib import Path
        
        holidays_config = Path(__file__).parent / 'config' / 'nse_holidays.yaml'
        validator = TradingHoursValidator(holidays_config)
        
        now = TimezoneHandler.now_eat()
        is_open = validator.is_market_open()
        
        result = {
            "is_open": is_open,
            "current_time_eat": TimezoneHandler.format_eat(now),
            "trading_hours": "9:00 AM - 3:00 PM EAT",
            "trading_days": "Monday - Friday"
        }
        
        if not is_open:
            next_open = validator.next_trading_day(now)
            result["next_open"] = TimezoneHandler.format_eat(next_open)
        
        return _json(result)
    except Exception as e:
        logger.error(f"nse_market_status error: {e}")
        return _err(str(e), 500)


async def nse_backfill(request):
    try:
        body = await request.json()
        symbols = body.get("symbols", [])
        start_date = date.fromisoformat(body.get("start_date"))
        end_date = date.fromisoformat(body.get("end_date", date.today().isoformat()))
        
        if not symbols:
            return _err("symbols list required")
        
        from app.services.backfill_service import BackfillService
        
        backfill = BackfillService()
        with get_sync_session() as session:
            result = backfill.backfill_historical(symbols, start_date, end_date, session)
        
        return _json({
            "total_collected": result.total_collected,
            "total_failed": result.total_failed,
            "duration_seconds": result.duration_seconds,
            "details": result.total_records
        })
    except Exception as e:
        logger.error(f"nse_backfill error: {e}")
        return _err(str(e), 500)


async def data_quality_metrics(request):
    try:
        symbol = request.rel_url.query.get("symbol")
        market = request.rel_url.query.get("market")
        days = int(request.rel_url.query.get("days", 30))
        
        from app.models.stock import DataQualityMetrics
        from sqlmodel import select
        from datetime import datetime, timedelta
        
        with get_sync_session() as session:
            query = select(DataQualityMetrics)
            
            if symbol:
                from app.models.stock import StockSymbol
                stock_symbol = session.exec(
                    select(StockSymbol).where(StockSymbol.symbol == symbol)
                ).first()
                if stock_symbol:
                    query = query.where(DataQualityMetrics.symbol_id == stock_symbol.id)
            
            if market:
                query = query.where(DataQualityMetrics.market == market)
            
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.where(DataQualityMetrics.recorded_at >= cutoff)
            
            metrics = session.exec(query).all()
        
        # Aggregate by error type
        by_type = {}
        for m in metrics:
            if m.error_type not in by_type:
                by_type[m.error_type] = 0
            by_type[m.error_type] += 1
        
        return _json({
            "total_failures": len(metrics),
            "by_error_type": by_type,
            "period_days": days
        })
    except Exception as e:
        logger.error(f"data_quality_metrics error: {e}")
        return _err(str(e), 500)


# ── symbols ───────────────────────────────────────────────────────────────────

async def search_symbols(request):
    """Search NSE stock symbols"""
    q = request.rel_url.query.get("q", "").strip()
    limit = int(request.rel_url.query.get("limit", 20))
    
    from app.models.stock import StockSymbol
    from sqlmodel import select, or_
    
    with get_sync_session() as session:
        # Build query - NSE only
        query = select(StockSymbol).where(StockSymbol.market == "NSE")
        
        if q:
            query = query.where(
                or_(
                    StockSymbol.symbol.ilike(f"%{q}%"),
                    StockSymbol.company_name.ilike(f"%{q}%"),
                    StockSymbol.base_symbol.ilike(f"%{q}%")
                )
            )
        
        query = query.limit(min(limit, 100))
        results = session.exec(query).all()
        
        return _json({
            "results": [
                {
                    "symbol": s.symbol,
                    "company_name": s.company_name,
                    "market": s.market,
                    "currency": s.currency,
                    "exchange": s.exchange,
                    "is_active": s.is_active,
                    "base_symbol": s.base_symbol
                }
                for s in results
            ]
        })


# ── app factory ───────────────────────────────────────────────────────────────

def create_app():
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_post("/auth/register", register)
    app.router.add_post("/auth/login", login)
    app.router.add_post("/auth/logout", logout)
    app.router.add_get("/auth/me", get_current_user)
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
    app.router.add_get("/predictions/models/available", available_models)
    app.router.add_post("/agent/query", agent_query)
    app.router.add_get("/symbols/search", search_symbols)
    # NSE-specific endpoints
    app.router.add_get("/api/v1/market/nse/status", nse_market_status)
    app.router.add_post("/api/v1/data/backfill", nse_backfill)
    app.router.add_get("/api/v1/data-quality/metrics", data_quality_metrics)
    return app


if __name__ == "__main__":
    from app.config.config import settings
    app_instance = create_app()
    logger.info(f"Starting server on http://0.0.0.0:8000")
    web.run_app(app_instance, host="0.0.0.0", port=8000)

# For uvicorn - export the factory function, not the instance
def app():
    return create_app()
