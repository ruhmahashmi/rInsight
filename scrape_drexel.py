import praw
import pandas as pd
from datetime import datetime
import random
import logging
import time
from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

def mock_gemini_analysis(post_text, post_title):
    keywords = {
        'academic': ['exam', 'finals', 'midterms', 'math', 'study', 'no prep', 'crashing out', 'locking in', 'co-op'],
        'financial': ['broke', 'tuition', 'loans', 'textbooks', 'afford'],
        'health': ['brain fog', 'anxiety', 'fatigue', 'stress', 'mental'],
        'housing': ['roommate', 'dorm', 'housing', 'vibes off', 'API'],
        'social': ['club', 'DragonLink', 'FOMO', 'bet', 'friends']
    }
    sentiment = random.uniform(-1, 0.3)
    text = (post_title + ' ' + post_text).lower()
    post_keywords = []
    category = 'academic'
    max_matches = 0

    for cat, kws in keywords.items():
        matches = sum(1 for kw in kws if kw in text)
        if matches > max_matches:
            max_matches = matches
            category = cat
        post_keywords.extend(kw for kw in kws if kw in text)
    
    post_keywords = list(set(post_keywords))
    logger.debug(f"Post: {post_title[:50]}..., Category: {category}, Keywords: {post_keywords}")
    return {'sentiment': sentiment, 'category': category, 'keywords': post_keywords}

def scrape_drexel(limit=200):
    posts = []
    try:
        subreddit = reddit.subreddit("Drexel")
        logger.info(f"Fetching posts from r/{subreddit.display_name}")
        for post in subreddit.new(limit=limit):
            analysis = mock_gemini_analysis(post.selftext or "", post.title)
            week = datetime.fromtimestamp(post.created_utc).isocalendar().week  # Use actual ISO week
            posts.append({
                "id": post.id,
                "title": post.title,
                "text": post.selftext or "",
                "date": datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
                "upvotes": post.score,
                "comments": post.num_comments,
                "sentiment": analysis['sentiment'],
                "category": analysis['category'],
                "keywords": analysis['keywords'],
                "week": week
            })
            time.sleep(1)
        df = pd.DataFrame(posts)
        if not df.empty:
            df.to_csv("data/drexel_posts.csv", index=False)
            logger.info(f"Scraped {len(df)} posts from r/Drexel")
        else:
            logger.warning("No posts scraped from r/Drexel")
        return df
    except Exception as e:
        logger.error(f"Error scraping r/Drexel: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = scrape_drexel()
    print(f"Scraped {len(df)} posts")
    print(df.head())