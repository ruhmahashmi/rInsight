from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
from scrape_drexel import scrape_drexel
import random
import os
import logging
import pickle
import time

app = Flask(__name__)
CORS(app)

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cache file for Reddit data
CACHE_FILE = "data/drexel_cache.pkl"
CACHE_DURATION = 3600  # Cache for 1 hour

# Mock Data (expanded for all categories)
mock_posts = [
    {
        'id': 'p1', 'title': 'Crashing out for math finals', 'text': 'No prep, I’m cooked for MATH 101', 
        'date': '2025-04-20 10:00:00', 'upvotes': 15, 'comments': 8, 'sentiment': -0.8, 
        'category': 'academic', 'keywords': ['crashing out', 'no prep', 'math'], 'week': 4
    },
    {
        'id': 'p2', 'title': 'Locking in but stressed', 'text': 'Midterms got me acting unwise', 
        'date': '2025-04-19 15:30:00', 'upvotes': 10, 'comments': 5, 'sentiment': -0.7, 
        'category': 'academic', 'keywords': ['locking in', 'midterms'], 'week': 4
    },
    {
        'id': 'p3', 'title': 'Broke af, tuition due', 'text': 'Can’t afford textbooks', 
        'date': '2025-04-18 09:00:00', 'upvotes': 12, 'comments': 3, 'sentiment': -0.9, 
        'category': 'financial', 'keywords': ['broke af', 'tuition'], 'week': 4
    },
    {
        'id': 'p4', 'title': 'Brain fog is killing me', 'text': 'Can’t focus, need help', 
        'date': '2025-04-17 12:00:00', 'upvotes': 8, 'comments': 4, 'sentiment': -0.85, 
        'category': 'health', 'keywords': ['brain fog', 'focus'], 'week': 4
    },
    {
        'id': 'p5', 'title': 'Roommate vibes off', 'text': 'Dorm life is rough', 
        'date': '2025-04-16 14:00:00', 'upvotes': 9, 'comments': 2, 'sentiment': -0.75, 
        'category': 'housing', 'keywords': ['vibes off', 'roommate'], 'week': 4
    },
    {
        'id': 'p6', 'title': 'Bet, joined a club', 'text': 'DragonLink is chill', 
        'date': '2025-04-15 11:00:00', 'upvotes': 14, 'comments': 6, 'sentiment': 0.2, 
        'category': 'social', 'keywords': ['bet', 'DragonLink'], 'week': 4
    },
    {
        'id': 'p7', 'title': 'Housing at API is trash', 'text': 'Elevators broken again', 
        'date': '2025-04-14 10:00:00', 'upvotes': 20, 'comments': 10, 'sentiment': -0.9, 
        'category': 'housing', 'keywords': ['housing', 'API'], 'week': 4
    },
    {
        'id': 'p8', 'title': 'Co-op interviews stressing me out', 'text': 'No idea how to prep', 
        'date': '2025-04-13 16:00:00', 'upvotes': 18, 'comments': 7, 'sentiment': -0.8, 
        'category': 'academic', 'keywords': ['co-op', 'stress'], 'week': 4
    }
]

# Serve index.html at root
@app.route('/')
def serve_index():
    logger.debug("Serving index.html")
    return send_from_directory('.', 'index.html')

# Serve static files (styles.css, script.js)
@app.route('/<path:path>')
def serve_static(path):
    logger.debug(f"Serving static file: {path}")
    if os.path.exists(path):
        return send_from_directory('.', path)
    logger.error(f"File not found: {path}")
    return jsonify({'error': 'File not found'}), 404

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

@app.route('/api/stress-scores/<week>')
def stress_scores(week):
    logger.debug(f"Fetching stress scores for week: {week}")
    posts = load_cached_data()
    if posts is None:
        try:
            df = scrape_drexel(limit=50)  # Fetch live r/Drexel posts
            if df.empty:
                logger.warning("No posts fetched from r/Drexel, using mock data")
                posts = mock_posts
            else:
                posts = df.to_dict('records')
                save_cached_data(posts)
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {e}")
            posts = mock_posts
    
    if week != 'all':
        posts = [p for p in posts if p['week'] == int(week)]
    
    scores = {'academic': [], 'financial': [], 'health': [], 'housing': [], 'social': []}
    for post in posts:
        score = (0.35 * post['sentiment'] + 
                 0.25 * (len(post['keywords']) / 5) + 
                 0.2 * (1.2 if post['week'] in [4, 8] else 0.5) + 
                 0.2 * (post['upvotes'] / 50)) * 100
        score = max(0, min(100, 100 - score))  # Invert: lower = higher stress
        scores[post['category']].append(score)
    
    result = {}
    for cat in scores:
        if scores[cat]:
            avg_score = round(sum(scores[cat]) / len(scores[cat]))
            status = 'Critical' if avg_score < 50 else 'Moderate' if avg_score < 70 else 'Low'
            color = '#EF4444' if avg_score < 50 else '#FBBF24' if avg_score < 70 else '#10B981'
            trend = f"+{random.randint(10, 25)}%" if avg_score < 70 else "Stable"
            recommendation = {
                'academic': 'Promote Math Resource Center (MRC)',
                'financial': 'Link to Student Financial Services',
                'health': 'Offer Counseling Center drop-ins',
                'housing': 'Refer to Resident Life',
                'social': 'Promote DragonLink clubs'
            }[cat]
            result[cat] = {
                'score': avg_score,
                'trend': trend,
                'status': status,
                'color': color,
                'recommendation': recommendation,
                'trend_labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                'trend_data': [60, 55, 50, avg_score]
            }
    result['summary'] = f"Week {week} stress: {'High' if any(s < 50 for s in [r.get('score', 100) for r in result.values()]) else 'Moderate'}"
    result['recommendation'] = 'Host campus-wide wellness fair'
    return jsonify(result)

@app.route('/api/keywords/<week>')
def keywords(week):
    logger.debug(f"Fetching keywords for week: {week}")
    posts = load_cached_data()
    if posts is None:
        try:
            df = scrape_drexel(limit=50)  # Fetch live r/Drexel posts
            if df.empty:
                logger.warning("No posts fetched from r/Drexel, using mock data")
                posts = mock_posts
            else:
                posts = df.to_dict('records')
                save_cached_data(posts)
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {e}")
            posts = mock_posts
    
    if week != 'all':
        posts = [p for p in posts if p['week'] == int(week)]
    
    keyword_counts = {}
    for post in posts:
        for kw in post['keywords']:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    
    result = [
        {
            'keyword': kw,
            'frequency': count,
            'category': next(p['category'] for p in posts if kw in p['keywords']),
            'sample': next(p['title'] for p in posts if kw in p['keywords']),
            'week': week if week != 'all' else 'all'
        }
        for kw, count in keyword_counts.items()
    ]
    return jsonify(result)

@app.route('/api/recommendations/<week>')
def recommendations(week):
    logger.debug(f"Fetching recommendations for week: {week}")
    posts = load_cached_data()
    if posts is None:
        try:
            df = scrape_drexel(limit=50)  # Fetch live r/Drexel posts
            if df.empty:
                logger.warning("No posts fetched from r/Drexel, using mock data")
                posts = mock_posts
            else:
                posts = df.to_dict('records')
                save_cached_data(posts)
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {e}")
            posts = mock_posts
    
    if week != 'all':
        posts = [p for p in posts if p['week'] == int(week)]
    
    keyword_recs = {
        'crashing out': 'Promote Math Resource Center (MRC) for math exam Deutsche',
        'locking in': 'Host Week 4 study session with Academic Resource Center (ARC)',
        'broke af': 'Link to Student Financial Services for tuition concerns',
        'bet': 'Promote DragonLink for social engagement',
        'brain fog': 'Offer Counseling Center drop-ins for mental health',
        'vibes off': 'Refer to Resident Life for roommate mediation',
        'housing': 'Refer to Resident Life for housing issues',
        'co-op': 'Promote Steinbright Career Center for co-op prep',
        'no prep': 'Promote Quizlet and peer tutoring for exam prep'
    }
    result = [
        {
            'keyword': kw,
            'suggestion': keyword_recs.get(kw, 'General wellness support'),
            'week': week if week != 'all' else 'all'
        }
        for post in posts for kw in post['keywords'] if kw in keyword_recs
    ]
    return jsonify(list({v['keyword']: v for v in result}.values()))

if __name__ == '__main__':
    logger.info("Starting Flask server on port 5000")
    app.run(debug=True, port=5000)