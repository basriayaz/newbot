import tweepy
import logging
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twitter API credentials
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Test mode flag
IS_TEST_MODE = False

class TwitterBot:
    def __init__(self):
        self.client = None
        self.v1_client = None
        self.initialize_client()

    def initialize_client(self):
        """Initialize Twitter client with API credentials"""
        try:
            if not all([TWITTER_API_KEY, TWITTER_API_SECRET, 
                       TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET,
                       TWITTER_BEARER_TOKEN]):
                logging.error("Twitter credentials not found in environment variables")
                return

            # Initialize v2 client for text tweets
            self.client = tweepy.Client(
                bearer_token=TWITTER_BEARER_TOKEN,
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
            )

            # Initialize v1.1 client for media upload
            auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
            auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
            self.v1_client = tweepy.API(auth)

            logging.info("Twitter clients initialized successfully")

        except Exception as e:
            logging.error(f"Error initializing Twitter client: {str(e)}")

    def send_tweet(self, text: str) -> bool:
        """Send a text tweet using v2 API"""
        try:
            if IS_TEST_MODE:
                logging.info(f"[TEST MODE] Would send tweet: {text}")
                return True

            if not self.client:
                logging.error("Twitter client not initialized")
                return False

            self.client.create_tweet(text=text)
            logging.info("Tweet sent successfully")
            return True

        except Exception as e:
            logging.error(f"Error sending tweet: {str(e)}")
            return False

    def send_tweet_with_media(self, text: str, media_path: str) -> bool:
        """Send a tweet with media using v1.1 API for media upload and v2 for tweet"""
        try:
            if IS_TEST_MODE:
                logging.info(f"[TEST MODE] Would send tweet with media: {text}, media: {media_path}")
                return True

            if not self.client or not self.v1_client:
                logging.error("Twitter client not initialized")
                return False

            if not os.path.exists(media_path):
                logging.error(f"Media file not found: {media_path}")
                return False

            # Upload media using v1.1 API
            media = self.v1_client.media_upload(media_path)
            
            # Create tweet with media using v2 API
            self.client.create_tweet(text=text, media_ids=[media.media_id])
            logging.info("Tweet with media sent successfully")
            return True

        except Exception as e:
            logging.error(f"Error sending tweet with media: {str(e)}")
            return False

# Create a global instance
twitter_bot = TwitterBot()

def set_test_mode(enabled: bool = True):
    """Enable or disable test mode"""
    global IS_TEST_MODE
    IS_TEST_MODE = enabled
    if enabled:
        logging.info("Twitter bot test mode enabled")
    else:
        logging.info("Twitter bot test mode disabled")

def send_twitter_message(text: str, media_path: Optional[str] = None) -> bool:
    """Send message to Twitter"""
    if media_path:
        return twitter_bot.send_tweet_with_media(text, media_path)
    return twitter_bot.send_tweet(text) 