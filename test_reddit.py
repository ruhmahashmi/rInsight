import praw
from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

for post in reddit.subreddit("Drexel").new(limit=5):
    print(post.title, post.created_utc)