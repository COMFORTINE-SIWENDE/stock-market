import threading
import time
from datetime import date

import schedule

from app.utils.logger import logger

_scheduler_thread: threading.Thread | None = None
_running = False


def _run_scheduler():
    global _running
    while _running:
        schedule.run_pending()
        time.sleep(60)


def start_scheduler(session_factory) -> None:
    """Register background jobs and start the scheduler thread."""
    global _scheduler_thread, _running

    def _collect_stock():
        from app.services.data_service import collect_stock_data
        from sqlmodel import select
        from app.models.stock import StockSymbol
        try:
            with session_factory() as session:
                symbols = session.exec(
                    select(StockSymbol).where(StockSymbol.is_active == True)
                ).all()
                end = date.today().isoformat()
                start = "2020-01-01"
                for sym in symbols:
                    collect_stock_data(session, sym.symbol, start, end)
        except Exception as e:
            logger.error(f"Scheduled stock collection failed: {e}")

    def _collect_news():
        from app.services.data_service import collect_news
        from sqlmodel import select
        from app.models.stock import StockSymbol
        try:
            with session_factory() as session:
                symbols = session.exec(
                    select(StockSymbol).where(StockSymbol.is_active == True)
                ).all()
                for sym in symbols:
                    collect_news(session, sym.symbol)
        except Exception as e:
            logger.error(f"Scheduled news collection failed: {e}")

    schedule.every().day.at("18:00").do(_collect_stock)
    schedule.every().hour.do(_collect_news)

    _running = True
    _scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True, name="scheduler")
    _scheduler_thread.start()
    logger.info("Scheduler started: stock data daily at 18:00, news every hour")


def stop_scheduler() -> None:
    global _running
    _running = False
    schedule.clear()
    logger.info("Scheduler stopped")
