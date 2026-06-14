"""Kenyan financial lexicon for sentiment analysis adjustments."""

# Kenyan-specific financial terms with sentiment scores
# Positive scores: +0.1 to +0.5
# Negative scores: -0.5 to -0.1
# Neutral scores: 0.0

KENYAN_FINANCIAL_TERMS = {
    # Positive terms
    'm-pesa': 0.3,
    'mpesa': 0.3,
    'm pesa': 0.3,
    'mobile money': 0.2,
    'shilling strengthens': 0.4,
    'shilling gains': 0.4,
    'shilling rallies': 0.4,
    'bourse gains': 0.4,
    'bourse rallies': 0.4,
    'nse rallies': 0.4,
    'nse gains': 0.4,
    'nse surge': 0.5,
    'nse climbs': 0.3,
    'nse rises': 0.3,
    'safaricom expansion': 0.3,
    'safaricom growth': 0.3,
    'dividend payout': 0.3,
    'dividend increase': 0.4,
    'earnings beat': 0.4,
    'profit growth': 0.4,
    'revenue growth': 0.3,
    'market confidence': 0.3,
    'investor optimism': 0.4,
    'bullish sentiment': 0.4,
    'economic recovery': 0.3,
    'gdp growth': 0.3,
    'infrastructure investment': 0.2,
    'foreign investment': 0.3,
    'credit rating upgrade': 0.4,
    
    # Negative terms
    'shilling weakens': -0.4,
    'shilling drops': -0.4,
    'shilling falls': -0.4,
    'shilling declines': -0.4,
    'bourse declines': -0.4,
    'bourse drops': -0.4,
    'nse drops': -0.4,
    'nse falls': -0.4,
    'nse declines': -0.4,
    'nse slumps': -0.5,
    'market selloff': -0.5,
    'market crash': -0.5,
    'investor exodus': -0.5,
    'bearish sentiment': -0.4,
    'profit warning': -0.4,
    'earnings miss': -0.4,
    'dividend cut': -0.4,
    'debt crisis': -0.5,
    'inflation surge': -0.4,
    'interest rate hike': -0.3,
    'credit rating downgrade': -0.5,
    'liquidity crunch': -0.4,
    'default risk': -0.5,
    'currency crisis': -0.5,
    'economic slowdown': -0.3,
    'recession fears': -0.4,
    'capital flight': -0.4,
    
    # Neutral/contextual terms
    'nse trading': 0.0,
    'nairobi bourse': 0.0,
    'securities exchange': 0.0,
    'central bank': 0.0,
    'central bank of kenya': 0.0,
    'cbk': 0.0,
    'treasury bonds': 0.0,
    'treasury bills': 0.0,
    'money market': 0.0,
    'capital markets': 0.0,
    'stock market': 0.0,
    'equity market': 0.0,
    'bond market': 0.0,
    'forex market': 0.0,
    'interbank rate': 0.0,
    'repo rate': 0.0,
    'market volatility': -0.1,
    'trading volume': 0.0,
    'market cap': 0.0,
    'market capitalization': 0.0,
    
    # Company-specific terms (Kenyan blue chips)
    'safaricom': 0.1,  # Slight positive bias for market leader
    'equity bank': 0.0,
    'kcb': 0.0,
    'kcb group': 0.0,
    'co-operative bank': 0.0,
    'coop bank': 0.0,
    'east african breweries': 0.0,
    'eabl': 0.0,
    'bamburi cement': 0.0,
    'kenya power': -0.1,  # Slight negative due to historical challenges
    'kengen': 0.0,
    'nation media': 0.0,
    'standard chartered': 0.0,
    'absa': 0.0,
    'ncba': 0.0,
    'diamond trust': 0.0,
    'dtb': 0.0,
    
    # Economic indicators (Kenyan context)
    'inflation rate': -0.1,
    'unemployment': -0.2,
    'export growth': 0.2,
    'import growth': -0.1,
    'trade deficit': -0.2,
    'fiscal deficit': -0.2,
    'budget deficit': -0.2,
    'tax revenue': 0.1,
    'remittances': 0.2,
    'tourism revenue': 0.2,
    'tea exports': 0.1,
    'coffee exports': 0.1,
    'horticultural exports': 0.1,
}


def get_sentiment_adjustment(text: str) -> float:
    """
    Get sentiment adjustment based on Kenyan financial terms.
    
    Args:
        text: Text to analyze (should be lowercased)
    
    Returns:
        Cumulative sentiment adjustment score
    """
    text_lower = text.lower()
    adjustment = 0.0
    
    for term, score in KENYAN_FINANCIAL_TERMS.items():
        if term in text_lower:
            adjustment += score
    
    # Cap adjustment to reasonable range
    return max(-1.0, min(1.0, adjustment))
