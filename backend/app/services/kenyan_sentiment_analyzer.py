"""Kenyan sentiment analyzer with context-aware adjustments."""
import logging
from typing import Dict, Any

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    SentimentIntensityAnalyzer = None

from app.config.kenyan_financial_lexicon import get_sentiment_adjustment


logger = logging.getLogger(__name__)


class SentimentScore:
    """Sentiment score result."""
    
    def __init__(
        self,
        textblob_polarity: float,
        textblob_subjectivity: float,
        vader_compound: float,
        vader_positive: float,
        vader_neutral: float,
        vader_negative: float,
        combined_score: float,
        classification: str
    ):
        self.textblob_polarity = textblob_polarity
        self.textblob_subjectivity = textblob_subjectivity
        self.vader_compound = vader_compound
        self.vader_positive = vader_positive
        self.vader_neutral = vader_neutral
        self.vader_negative = vader_negative
        self.combined_score = combined_score
        self.classification = classification
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'textblob_polarity': self.textblob_polarity,
            'textblob_subjectivity': self.textblob_subjectivity,
            'vader_compound': self.vader_compound,
            'vader_positive': self.vader_positive,
            'vader_neutral': self.vader_neutral,
            'vader_negative': self.vader_negative,
            'combined_score': self.combined_score,
            'classification': self.classification
        }


class KenyanSentimentAnalyzer:
    """Sentiment analyzer with Kenyan financial context awareness."""
    
    # Classification thresholds
    POSITIVE_THRESHOLD = 0.1
    NEGATIVE_THRESHOLD = -0.1
    
    def __init__(self):
        """Initialize sentiment analyzer with TextBlob and VADER."""
        self.vader_analyzer = None
        
        if TextBlob is None:
            logger.warning("TextBlob not installed. Install with: pip install textblob")
        
        if SentimentIntensityAnalyzer is None:
            logger.warning("VADER not installed. Install with: pip install vaderSentiment")
        else:
            self.vader_analyzer = SentimentIntensityAnalyzer()
        
        logger.info("Kenyan Sentiment Analyzer initialized")
    
    def analyze(self, article: Dict[str, Any]) -> SentimentScore:
        """
        Analyze sentiment of a news article.
        
        Combines TextBlob and VADER scores, then adjusts for Kenyan context.
        
        Args:
            article: Article dictionary with 'title' and 'content' keys
        
        Returns:
            SentimentScore object with detailed sentiment metrics
        """
        # Combine title and content (title weighted more heavily)
        title = article.get('title', '')
        content = article.get('content', '')
        
        # Title has more weight
        text = f"{title} {title} {content}"
        
        # Get base sentiment scores
        textblob_polarity = 0.0
        textblob_subjectivity = 0.0
        
        if TextBlob is not None:
            try:
                blob = TextBlob(text)
                textblob_polarity = blob.sentiment.polarity
                textblob_subjectivity = blob.sentiment.subjectivity
            except Exception as e:
                logger.warning(f"TextBlob analysis failed: {e}")
        
        # VADER scores
        vader_compound = 0.0
        vader_positive = 0.0
        vader_neutral = 0.0
        vader_negative = 0.0
        
        if self.vader_analyzer is not None:
            try:
                vader_scores = self.vader_analyzer.polarity_scores(text)
                vader_compound = vader_scores['compound']
                vader_positive = vader_scores['pos']
                vader_neutral = vader_scores['neu']
                vader_negative = vader_scores['neg']
            except Exception as e:
                logger.warning(f"VADER analysis failed: {e}")
        
        # Combine TextBlob and VADER scores (equal weight)
        base_score = (textblob_polarity + vader_compound) / 2.0
        
        # Apply Kenyan context adjustment
        combined_score = self._adjust_for_kenyan_context(text, base_score)
        
        # Ensure score is within bounds
        combined_score = max(-1.0, min(1.0, combined_score))
        
        # Classify sentiment
        classification = self._classify_sentiment(combined_score)
        
        return SentimentScore(
            textblob_polarity=textblob_polarity,
            textblob_subjectivity=textblob_subjectivity,
            vader_compound=vader_compound,
            vader_positive=vader_positive,
            vader_neutral=vader_neutral,
            vader_negative=vader_negative,
            combined_score=combined_score,
            classification=classification
        )
    
    def _adjust_for_kenyan_context(self, text: str, base_score: float) -> float:
        """
        Adjust sentiment score based on Kenyan financial lexicon.
        
        Args:
            text: Article text
            base_score: Base sentiment score from TextBlob/VADER
        
        Returns:
            Adjusted sentiment score
        """
        # Get adjustment from Kenyan lexicon
        adjustment = get_sentiment_adjustment(text)
        
        # Apply adjustment with dampening
        # Strong adjustments (+/-0.5) can shift sentiment significantly
        # Weak adjustments (+/-0.1) have minor influence
        adjusted_score = base_score + (adjustment * 0.5)
        
        return adjusted_score
    
    def _classify_sentiment(self, score: float) -> str:
        """
        Classify sentiment based on score.
        
        Args:
            score: Combined sentiment score (-1.0 to 1.0)
        
        Returns:
            Classification: 'positive', 'negative', or 'neutral'
        """
        if score > self.POSITIVE_THRESHOLD:
            return 'positive'
        elif score < self.NEGATIVE_THRESHOLD:
            return 'negative'
        else:
            return 'neutral'
