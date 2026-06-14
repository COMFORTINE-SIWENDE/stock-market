"""Trading hours validator for NSE market with holiday support."""
import logging
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Set

import yaml

from app.services.timezone_handler import TimezoneHandler


logger = logging.getLogger(__name__)


class TradingHoursValidator:
    """Validates NSE trading hours and holidays."""
    
    # NSE trading hours: 9:00 AM - 3:00 PM EAT
    TRADING_START = time(9, 0)
    TRADING_END = time(15, 0)
    
    # Trading days: Monday (0) to Friday (4)
    TRADING_DAYS = [0, 1, 2, 3, 4]
    
    def __init__(self, holidays_config: Path):
        """
        Initialize the trading hours validator.
        
        Args:
            holidays_config: Path to NSE holidays YAML configuration file
        """
        self.holidays: Set[str] = set()
        self._load_holidays(holidays_config)
    
    def _load_holidays(self, config_path: Path) -> None:
        """
        Load NSE holidays from YAML configuration.
        
        Args:
            config_path: Path to holidays configuration file
        """
        try:
            if not config_path.exists():
                logger.warning(f"Holidays config not found: {config_path}")
                return
            
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data or 'holidays' not in data:
                logger.warning("No holidays found in config")
                return
            
            for holiday in data['holidays']:
                date_str = holiday.get('date')
                if date_str:
                    self.holidays.add(date_str)
            
            logger.info(f"Loaded {len(self.holidays)} NSE holidays")
            
        except Exception as e:
            logger.error(f"Failed to load holidays config: {e}")
    
    def is_trading_hours(self, dt: datetime) -> bool:
        """
        Check if given datetime is within NSE trading hours.
        
        Args:
            dt: Datetime to check (will be converted to EAT if needed)
        
        Returns:
            True if within trading hours, False otherwise
        """
        # Convert to EAT
        dt_eat = TimezoneHandler.to_eat(dt)
        
        # Check if it's a trading day
        if not self.is_trading_day(dt_eat):
            return False
        
        # Check if within trading hours
        current_time = dt_eat.time()
        return self.TRADING_START <= current_time <= self.TRADING_END
    
    def is_trading_day(self, dt: datetime) -> bool:
        """
        Check if given datetime is a trading day (not weekend or holiday).
        
        Args:
            dt: Datetime to check (will be converted to EAT if needed)
        
        Returns:
            True if it's a trading day, False otherwise
        """
        # Convert to EAT
        dt_eat = TimezoneHandler.to_eat(dt)
        
        # Check if weekend
        if dt_eat.weekday() not in self.TRADING_DAYS:
            return False
        
        # Check if holiday
        date_str = dt_eat.strftime("%Y-%m-%d")
        if date_str in self.holidays:
            return False
        
        return True
    
    def is_market_open(self) -> bool:
        """
        Check if NSE market is currently open.
        
        Returns:
            True if market is open now, False otherwise
        """
        now = TimezoneHandler.now_eat()
        return self.is_trading_hours(now)
    
    def next_trading_day(self, dt: datetime) -> datetime:
        """
        Get the next trading day after the given datetime.
        
        Skips weekends and holidays.
        
        Args:
            dt: Starting datetime (will be converted to EAT if needed)
        
        Returns:
            Next trading day at market open (9:00 AM EAT)
        """
        # Convert to EAT
        dt_eat = TimezoneHandler.to_eat(dt)
        
        # Start from next day at 9:00 AM
        next_day = dt_eat.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Keep checking until we find a trading day
        max_days = 30  # Safety limit
        for _ in range(max_days):
            if self.is_trading_day(next_day):
                return next_day
            next_day += timedelta(days=1)
        
        # If we couldn't find a trading day in 30 days, just return the result
        logger.warning(f"Could not find trading day within {max_days} days from {dt_eat}")
        return next_day
