"""Price formatter for KES and USD currencies."""


def format_kes(amount: float) -> str:
    """
    Format amount in Kenyan Shillings.
    
    Args:
        amount: Amount to format
    
    Returns:
        Formatted string with KES label
    """
    if amount is None:
        return "KES 0.00"
    
    if amount == 0:
        return "KES 0.00"
    
    return f"KES {amount:,.2f}"


def format_usd(amount: float) -> str:
    """
    Format amount in US Dollars.
    
    Args:
        amount: Amount to format
    
    Returns:
        Formatted string with USD label
    """
    if amount is None:
        return "$0.00"
    
    if amount == 0:
        return "$0.00"
    
    return f"${amount:,.2f}"


def format_currency(amount: float, currency: str) -> str:
    """
    Format amount with appropriate currency.
    
    Args:
        amount: Amount to format
        currency: Currency code (KES or USD)
    
    Returns:
        Formatted string
    """
    if currency == 'KES':
        return format_kes(amount)
    elif currency == 'USD':
        return format_usd(amount)
    else:
        return f"{currency} {amount:,.2f}"
