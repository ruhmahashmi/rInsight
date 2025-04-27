import pandas as pd
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load NLP models
nlp = spacy.load("en_core_web_sm")
analyzer = SentimentIntensityAnalyzer()

# Function to extract issues from text
def extract_issues(text):
    if not isinstance(text, str):
        text = ""
    text = text.lower()
    issues = []
    if any(word in text for word in ["stress", "anxiety", "depressed", "burnout"]):
        issues.append("mental_health")
    if "co-op" in text or "coop" in text:
        issues.append("co_op")
    if "finals" in text or "exams" in text:
        issues.append("finals")
    return issues

# Main function to analyze posts
def analyze_posts(input_csv="data/drexel_posts.csv", output_csv="data/analyzed_posts.csv"):
    try:
        df = pd.read_csv(input_csv)

        # Fill missing title/text with empty strings
        df["title"] = df["title"].fillna("")
        df["text"] = df["text"].fillna("")

        # Combine title and text into one 'content' column
        df["content"] = df["title"] + " " + df["text"]

        # Apply issue extraction and sentiment analysis
        df["issues"] = df["content"].apply(extract_issues)
        df["sentiment"] = df["content"].apply(
            lambda x: analyzer.polarity_scores(x)["compound"] if isinstance(x, str) else 0
        )

        # Save to CSV
        df.to_csv(output_csv, index=False)

        return df

    except Exception as e:
        print(f"Error analyzing: {e}")
        return pd.DataFrame()

# Script entry point
if __name__ == "__main__":
    df = analyze_posts()
    print(f"Analyzed {len(df)} posts")

    if not df.empty:
        print(df[["content", "issues", "sentiment"]].head())
    else:
        print("No posts to display.")
