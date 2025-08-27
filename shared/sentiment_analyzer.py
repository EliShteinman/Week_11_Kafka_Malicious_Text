import nltk
import os
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        NLTK_DIR = os.path.join(os.getcwd(), "nltk_data")
        try:
            nltk.download("vader_lexicon", download_dir=NLTK_DIR, quiet=True)
            logger.info("VADER lexicon installed successfully")
        except Exception as e:
            logger.error(f"Error installing VADER lexicon: {e}")
        self.sid = SentimentIntensityAnalyzer()

    def get_sentiment_score(self, text: str) -> float:
        if not text or not isinstance(text, str):
            logger.debug("Empty or invalid text for sentiment analysis")
            return 0.0
        try:
            score = self.sid.polarity_scores(text)
            return score['compound']
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return 0.0

    def get_sentiment_label(self, text: str, positive: float = 0.5, negative: float = -0.5) -> str:
        if not text or not isinstance(text, str):
            logger.debug("Empty or invalid text for sentiment analysis")
            return "neutral"
        score = self.get_sentiment_score(text)
        if score >= positive:
            return "positive"
        elif score <= negative:
            return "negative"
        else:
            return "neutral"


if __name__ == "__main__":
    tests = [
        # Positive
        "The conference was extremely well organized, the speakers were engaging, and the atmosphere was inspiring. I left feeling motivated to start new projects.",
        "I finally upgraded my laptop after years of waiting, and it was worth every penny. The performance boost is incredible and the battery lasts all day.",

        # Negative
        "After the latest update, the application became painfully slow and crashes almost every time I try to save my work. It’s frustrating and makes it almost unusable.",
        "The hotel looked nice in the pictures, but in reality the room was dirty, the air conditioning didn’t work, and the staff was rude when I asked for help.",

        # Neutral
        "The meeting is scheduled for Thursday at 3 PM in the main office. Please bring the quarterly reports and updated financial statements.",
        "The package was shipped on September 2nd and is expected to arrive within five business days. Tracking information has been provided via email.",

        # Mixed
        "The phone’s screen is gorgeous and the speakers are loud and clear, but the camera quality is disappointing, especially in low light. Overall it’s a decent device, but not perfect.",
        "The restaurant’s food was outstanding and the portions were generous. However, we had to wait nearly an hour for a table, and the service felt rushed once we sat down.",
        "The workshop covered useful material and the instructor was knowledgeable. Unfortunately, the pace was too fast and many participants struggled to keep up.",

        # Edge
        "I don’t usually write reviews, but this experience was neither amazing nor terrible. It had its ups and downs, and in the end it was just okay.",
    ]

    sa = SentimentAnalyzer()
    for t in tests:
        print(f"{t!r:100} -> {sa.get_sentiment_label(t)} ({sa.get_sentiment_score(t):.3f})")