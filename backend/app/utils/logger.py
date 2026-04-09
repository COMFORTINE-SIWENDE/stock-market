import sys
from pathlib import Path
from loguru import logger as _logger

from app.config.config import settings

# Remove default handler
_logger.remove()

# Console sink
_logger.add(
    sys.stderr,
    level="DEBUG" if settings.DEBUG else "INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

# Rotating file sink
_log_dir = Path(__file__).parent.parent.parent / "logs"
_log_dir.mkdir(exist_ok=True)

_logger.add(
    str(_log_dir / "app_{time:YYYY-MM-DD}.log"),
    level=settings.LOG_LEVEL,
    rotation="00:00",       # daily rotation
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

logger = _logger
