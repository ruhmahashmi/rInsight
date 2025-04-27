import praw
import pandas as pd
import json
from datetime import datetime
import logging
import time
import google.generativeai as genai
from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT, GEMINI_API_KEY

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not set in config.py")
    raise ValueError("GEMINI_API_KEY is required")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def gemini_analysis(post_text, post_title):
    text = post_title + " " + post_text
    prompt = f"""
    Analyze the following Reddit post for sentiment (positive, neutral, negative), categorize into one of: academic, financial, health, housing, social, and extract relevant keywords. Return JSON with sentiment, category, and keywords.
    Post: {text}
    """
    try:
        response = model.generate_content(prompt)
        logger.debug(f"Gemini raw response: {response.text}")
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.warning(f"Gemini response is not valid JSON: {e}, using fallback parsing")
            sentiment = "neutral"
            category = "academic"
            keywords = []
            if "positive" in response.text.lower():
                sentiment = "positive"
            elif "negative" in response.text.lower():
                sentiment = "negative"
            for cat in ["academic", "financial", "health", "housing", "social"]:
                if cat in response.text.lower():
                    category = cat
                    break
            words = response.text.lower().split()
            keywords = [w for w in words if w in ['exam', 'stress', 'loans', 'dorm', 'friends', 'anxiety', 'tuition', 'midterms', 'FOMO', 'co-op']]
            return {
                "sentiment": sentiment,
                "category": category,
                "keywords": list(set(keywords))
            }
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        keywords = {
            'academic': ['exam', 'finals', 'midterms', 'study', 'co-op'],
            'financial': ['broke', 'tuition', 'loans', 'textbooks'],
            'health': ['anxiety', 'stress', 'mental', 'fatigue'],
            'housing': ['roommate', 'dorm', 'housing'],
            'social': ['club', 'friends', 'FOMO']
        }
        text = text.lower()
        category = 'academic'
        max_matches = 0
        post_keywords = []
        for cat, kws in keywords.items():
            matches = sum(1 for kw in kws if kw in text)
            if matches > max_matches:
                max_matches = matches
                category = cat
            post_keywords.extend(kw for kw in kws if kw in text)
        return {
            "sentiment": "neutral",
            "category": category,
            "keywords": list(set(post_keywords))
        }

def scrape_drexel(limit=10):
    posts = []
    api_call_count = 0
    try:
        subreddit = reddit.subreddit("Drexel")
        logger.info(f"Fetching posts from r/{subreddit.display_name}")
        for post in subreddit.new(limit=limit):
            analysis = gemini_analysis(post.selftext or "", post.title)
            api_call_count += 1
            logger.info(f"Gemini API call count: {api_call_count}")
            post_date = datetime.fromtimestamp(post.created_utc)
            posts.append({
                "id": post.id,
                "title": post.title,
                "text": post.selftext or "",
                "date": post_date.strftime("%Y-%m-%d %H:%M:%S"),
                "upvotes": post.score,
                "comments": post.num_comments,
                "sentiment": analysis['sentiment'],
                "category": analysis['category'],
                "keywords": analysis['keywords'],
                "week": post_date.isocalendar().week
            })
            time.sleep(4)
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