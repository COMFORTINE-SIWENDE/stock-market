"""Timezone handling for East Africa Time (EAT) used by NSE."""
from datetime import datetime, timedelta, timezone


class TimezoneHandler:
    """Handles timezone conversions for NSE (East Africa Time)."""
    
    # East Africa Time is UTC+3 (no daylight saving time)
    EAT = timezone(timedelta(hours=3))
    
    @staticmethod
    def to_eat(dt: datetime) -> datetime:
        """
        Convert a datetime to East Africa Time (EAT).
        
        Args:
            dt: Datetime to convert (can be naive or aware)
        
        Returns:
            Datetime in EAT timezone
        """
        if dt is None:
            return None
        
        # If naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Convert to EAT
        return dt.astimezone(TimezoneHandler.EAT)
    
    @staticmethod
    def to_utc(dt: datetime) -> datetime:
        """
        Convert a datetime to UTC.
        
        Args:
            dt: Datetime to convert (can be naive or aware)
        
        Returns:
            Datetime in UTC timezone
        """
        if dt is None:
            return None
        
        # If naive, assume EAT
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TimezoneHandler.EAT)
        
        # Convert to UTC
        return dt.astimezone(timezone.utc)
    
    @staticmethod
    def now_eat() -> datetime:
        """
        Get current datetime in East Africa Time.
        
        Returns:
            Current datetime in EAT timezone
        """
        return datetime.now(TimezoneHandler.EAT)
    
    @staticmethod
    def format_eat(dt: datetime) -> str:
        """
        Format a datetime as a string with EAT timezone indicator.
        
        Args:
            dt: Datetime to format
        
        Returns:
            Formatted string (e.g., "2024-05-11 14:30:00 EAT")
        """
        if dt is None:
            return ""
        
        # Convert to EAT if not already
        if dt.tzinfo != TimezoneHandler.EAT:
            dt = TimezoneHandler.to_eat(dt)
        
        return dt.strftime("%Y-%m-%d %H:%M:%S EAT")
