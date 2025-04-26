import praw
import pandas as pd
from datetime import datetime
from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

def scrape_drexel(limit=200):
    posts = []
    try:
        for post in reddit.subreddit("Drexel").new(limit=limit):
            posts.append({
                "title": post.title,
                "text": post.selftext or "",
                "date": datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
                "upvotes": post.score
            })
        df = pd.DataFrame(posts)
        df.to_csv("data/drexel_posts.csv", index=False)
        return df
    except Exception as e:
        print(f"Error scraping: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = scrape_drexel()
    print(f"Scraped {len(df)} posts")
    print(df.head())