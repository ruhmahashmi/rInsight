import praw
import logging
from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

try:
    subreddit = reddit.subreddit("Drexel")
    logger.info(f"Connected to: {subreddit.display_name}")
    for post in subreddit.new(limit=10):
        logger.info(f"Post: {post.title}, Created: {post.created_utc}")
        print(post.title, post.created_utc)
except Exception as e:
    logger.error(f"Error: {e}")
    print(f"Error: {e}")