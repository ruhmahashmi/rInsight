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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CACHE_FILE = "data/drexel_cache.pkl"
CACHE_DURATION = 3600

# Load crash predictions
def load_crash_predictions():
    try:
        df = pd.read_csv("data/crash_predictions.csv")
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error loading crash predictions: {e}")
        return []

@app.route('/')
def serve_index():
    logger.debug("Serving index.html")
    return send_from_directory('.', 'index.html')

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
            df = scrape_drexel(limit=50)
            if df.empty:
                logger.warning("No posts fetched from r/Drexel")
                return jsonify({'error': 'No posts available'}), 500
            posts = df.to_dict('records')
            save_cached_data(posts)
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {e}")
            return jsonify({'error': str(e)}), 500
    
    if week != 'all':
        posts = [p for p in posts if p['week'] == int(week)]
    
    scores = {'academic': [], 'financial': [], 'health': [], 'housing': [], 'social': []}
    for post in posts:
        score = (0.35 * post['sentiment'] + 
                0.25 * (len(post['keywords']) / 5) + 
                0.2 * (1.2 if post['week'] in [41, 50, 10, 24] else 0.5) + 
                0.2 * (post['upvotes'] / 50)) * 100
        score = max(0, min(100, 100 - score))
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
                'trend_labels': ['Week 1', 'Week 2', 'Week 3', f"Week {week}"],
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
            df = scrape_drexel(limit=50)
            if df.empty:
                logger.warning("No posts fetched from r/Drexel")
                return jsonify({'error': 'No posts available'}), 500
            posts = df.to_dict('records')
            save_cached_data(posts)
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {e}")
            return jsonify({'error': str(e)}), 500
    
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
    crash_predictions = load_crash_predictions()
    if not crash_predictions:
        logger.warning("No crash predictions available")
        return jsonify([])

    if week != 'all':
        crash_predictions = [p for p in crash_predictions if p['week'] == int(week)]
    
    result = [
        {
            'keyword': 'mental_health' if p['mental_health_count'] >= 2 else p['event'].lower().replace(' ', '_'),
            'suggestion': p['recommendation'],
            'week': str(p['week'])
        }
        for p in crash_predictions if p['recommendation']
    ]
    return jsonify(result)

if __name__ == '__main__':
    logger.info("Starting Flask server on port 5000")
    app.run(debug=True, port=5000)