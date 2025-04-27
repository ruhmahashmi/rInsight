import json
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import praw
import time
import pickle
import logging
from datetime import datetime, timedelta
import google.generativeai as genai
from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT, GEMINI_API_KEY

app = Flask(__name__, static_folder='static')
CORS(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Reddit API setup
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

# Gemini API setup
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not set in config.py")
    raise ValueError("GEMINI_API_KEY is required")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

CACHE_FILE = "data/drexel_cache.pkl"
CACHE_DURATION = 7200  # 2 hours

# Academic stress peaks (approximated for Drexel)
STRESS_PEAKS = [
    {"start": "2025-04-15", "end": "2025-04-20"}, # Midterms
    {"start": "2025-12-10", "end": "2025-12-15"}  # Finals
]

def load_cached_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            cache = pickle.load(f)
            if time.time() - cache['timestamp'] < CACHE_DURATION:
                logger.debug("Using cached Reddit data")
                return cache['data']
    return None

def save_cached_data(data):
    cache = {'timestamp': time.time(), 'data': data}
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)
    logger.debug("Cached Reddit data")

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

def gemini_recommendation(category, keywords):
    drexel_resources = [
        {"name": "Math Resource Center", "url": "https://drexel.edu/academics/resources/math-resource-center"},
        {"name": "Counseling Center", "url": "https://drexel.edu/counselingandhealth/counseling-center"},
        {"name": "Student Financial Services", "url": "https://drexel.edu/studentlife/financial-services"},
        {"name": "Resident Life", "url": "https://drexel.edu/studentlife/resident-life"},
        {"name": "DragonLink (Clubs)", "url": "https://dragonlink.drexel.edu"}
    ]
    prompt = f"""
    Given a student issue category ({category}), keywords ({keywords}), and Drexel resources ({json.dumps(drexel_resources)}), suggest a specific intervention linking to a relevant resource. Return JSON with 'recommendation' (a single sentence) and 'explanation' (why the recommendation was made based on keywords).
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
        result = json.loads(cleaned_response)
        return result
    except Exception as e:
        logger.error(f"Gemini recommendation error: {e}")
        return {
            "recommendation": f"Refer students to the Counseling Center for {category} support.",
            "explanation": f"Default recommendation due to error in analyzing keywords: {keywords}"
        }

def scrape_drexel(limit=5):
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
        return df
    except Exception as e:
        logger.error(f"Error scraping r/Drexel: {e}")
        return pd.DataFrame()

def is_stress_peak(post_date):
    post_date = datetime.strptime(post_date, "%Y-%m-%d %H:%M:%S")
    for peak in STRESS_PEAKS:
        start = datetime.strptime(peak["start"], "%Y-%m-%d")
        end = datetime.strptime(peak["end"], "%Y-%m-%d")
        if start <= post_date <= end:
            return 1.2
    return 0.5

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            logger.error(f"Invalid date format: {date_str}")
            raise e

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/stress-scores/<start_date>/<end_date>')
def stress_scores(start_date, end_date):
    try:
        posts = load_cached_data()
        if posts is None:
            df = scrape_drexel(limit=5)
            if df.empty:
                return jsonify({'error': 'No posts available'}), 500
            posts = df.to_dict('records')
            save_cached_data(posts)
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        posts = [p for p in posts if start <= parse_date(p['date']) <= end]
        
        scores = {'academic': [], 'financial': [], 'health': [], 'housing': [], 'social': []}
        category_counts = {'academic': 0, 'financial': 0, 'health': 0, 'housing': 0, 'social': 0}
        max_keywords = 5
        max_engagement = 50
        for post in posts:
            sentiment_val = {'positive': 1, 'neutral': 0, 'negative': -1}.get(post['sentiment'], 0)
            keyword_score = len(post['keywords']) / max_keywords
            engagement = (post['upvotes'] + post['comments']) / max_engagement
            temporal = is_stress_peak(parse_date(post['date']).strftime("%Y-%m-%d %H:%M:%S"))
            score = (0.3 * sentiment_val + 0.3 * keyword_score + 0.2 * engagement + 0.2 * temporal) * 100
            score = max(0, min(100, 100 - (score + 100) / 2))
            scores[post['category']].append(score)
            category_counts[post['category']] += 1
        
        result = {}
        trend_labels = [(start + timedelta(days=x)).strftime("%Y-%m-d") for x in range((end - start).days + 1)]
        overall_scores = []
        for cat in scores:
            if scores[cat]:
                avg_score = round(sum(scores[cat]) / len(scores[cat]))
                overall_scores.append(avg_score)
                status = 'Critical' if avg_score < 50 else 'Moderate' if avg_score < 70 else 'Low'
                color = '#F472B6' if avg_score < 50 else '#FBBF24' if avg_score < 70 else '#2DD4BF'
                recommendation = gemini_recommendation(cat, [p['keywords'] for p in posts if p['category'] == cat])
                result[cat] = {
                    'score': avg_score,
                    'status': status,
                    'color': color,
                    'recommendation': recommendation['recommendation'],
                    'recommendation_explanation': recommendation['explanation'],
                    'trend_labels': trend_labels,
                    'trend_data': [avg_score] * len(trend_labels)
                }
        # Overall Mental Health
        if overall_scores:
            overall_score = round(sum(overall_scores) / len(overall_scores))
            overall_status = 'Critical' if overall_score < 50 else 'Moderate' if overall_score < 70 else 'Low'
            overall_color = '#F472B6' if overall_score < 50 else '#FBBF24' if overall_score < 70 else '#2DD4BF'
            # General recommendation
            general_recommendation = gemini_recommendation('general', [kw for p in posts for kw in p['keywords']])
            # Secondary recommendation for the second most stressed category
            sorted_categories = sorted(scores.items(), key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 100)
            second_category = sorted_categories[1][0] if len(sorted_categories) > 1 else 'academic'
            secondary_recommendation = gemini_recommendation(second_category, [p['keywords'] for p in posts if p['category'] == second_category])
            result['overall'] = {
                'score': overall_score,
                'status': overall_status,
                'color': overall_color,
                'recommendation': general_recommendation['recommendation'],
                'recommendation_explanation': general_recommendation['explanation'],
                'secondary_recommendation': secondary_recommendation['recommendation'],
                'secondary_recommendation_explanation': secondary_recommendation['explanation'],
                'trend_labels': trend_labels,
                'trend_data': [overall_score] * len(trend_labels)
            }
        result['summary'] = f"Campus mental health from {start_date} to {end_date}: {'High stress' if any(s < 50 for s in [r.get('score', 100) for r in result.values()]) else 'Moderate stress'}"
        result['category_counts'] = category_counts
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in stress_scores: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/keywords/<start_date>/<end_date>')
def keywords(start_date, end_date):
    try:
        posts = load_cached_data()
        if posts is None:
            df = scrape_drexel(limit=5)
            if df.empty:
                return jsonify({'error': 'No posts available'}), 500
            posts = df.to_dict('records')
            save_cached_data(posts)
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        posts = [p for p in posts if start <= parse_date(p['date']) <= end]
        
        keyword_counts = {}
        for post in posts:
            for kw in post['keywords']:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        
        result = [
            {
                'keyword': kw,
                'frequency': count,
                'category': next(p['category'] for p in posts if kw in p['keywords']),
                'sample': next(p['title'] for p in posts if kw in p['keywords'])
            }
            for kw, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in keywords: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/recent-insights/<start_date>/<end_date>')
def recent_insights(start_date, end_date):
    try:
        posts = load_cached_data()
        if posts is None:
            df = scrape_drexel(limit=5)
            if df.empty:
                return jsonify({'error': 'No posts available'}), 500
            posts = df.to_dict('records')
            save_cached_data(posts)
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        posts = [p for p in posts if start <= parse_date(p['date']) <= end]
        
        # Sort by date descending and take the top 2
        posts.sort(key=lambda x: parse_date(x['date']), reverse=True)
        insights = [
            {
                'title': post['title'],
                'category': post['category']
            }
            for post in posts[:2]
        ]
        return jsonify(insights)
    except Exception as e:
        logger.error(f"Error in recent_insights: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)