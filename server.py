import os
import re
import random
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import tweepy

# ---------------------------------------------------
# FLASK APP
# ---------------------------------------------------

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

CORS(app)

print("Lightweight sentiment server started!")

# ---------------------------------------------------
# TWITTER/X API
# ---------------------------------------------------

BEARER_TOKEN = os.environ.get("BEARER_TOKEN")

if BEARER_TOKEN:

    try:

        tweepy_client = tweepy.Client(
            bearer_token=BEARER_TOKEN
        )

        print("Twitter client initialized!")

    except Exception as e:

        print(f"Tweepy init failed: {e}")
        tweepy_client = None

else:

    print("No BEARER_TOKEN found. Using mock mode.")
    tweepy_client = None

# ---------------------------------------------------
# LIGHTWEIGHT SENTIMENT ANALYSIS
# ---------------------------------------------------

POSITIVE_WORDS = [
    "love", "great", "awesome", "good",
    "happy", "excellent", "amazing",
    "beautiful", "best", "fantastic",
    "nice", "wonderful", "cool"
]

NEGATIVE_WORDS = [
    "bad", "terrible", "awful", "hate",
    "worst", "sad", "angry",
    "disappointed", "broken", "useless",
    "horrible", "annoying"
]

def predict_sentiment(text):

    text = text.lower()

    pos_count = sum(
        word in text for word in POSITIVE_WORDS
    )

    neg_count = sum(
        word in text for word in NEGATIVE_WORDS
    )

    if pos_count > neg_count:
        return "Positive"

    elif neg_count > pos_count:
        return "Negative"

    else:
        return "Neutral"

# ---------------------------------------------------
# MOCK DATA
# ---------------------------------------------------

GENERIC_MOCK_TWEETS = [

    "Today is an amazing day!",
    "Traffic is horrible today.",
    "I love learning machine learning.",
    "This product quality is terrible.",
    "The weather is beautiful outside.",
    "Coding is fun and challenging.",
    "Customer support disappointed me.",
    "This movie was incredible.",
    "I feel very productive today.",
    "The update broke everything."
]

def generate_mock_tweets(username, count):

    tweets_data = []

    base_time = datetime.utcnow()

    for i in range(count):

        tweet_time = base_time - timedelta(hours=i)

        tweets_data.append({

            "text": random.choice(
                GENERIC_MOCK_TWEETS
            ),

            "created_at": tweet_time.strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )
        })

    return tweets_data

# ---------------------------------------------------
# ROUTES
# ---------------------------------------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ---------------------------------------------------
# ANALYZE TEXT API
# ---------------------------------------------------

@app.route('/api/analyze-text', methods=['POST'])
def api_analyze_text():

    data = request.get_json() or {}

    text = data.get("text", "").strip()

    if not text:

        return jsonify({
            "error": "No text provided."
        }), 400

    sentiment = predict_sentiment(text)

    confidence = round(
        random.uniform(70, 98),
        2
    )

    return jsonify({

        "text": text,

        "sentiment": sentiment,

        "confidence": confidence,

        "emoji":
            "😊" if sentiment == "Positive"
            else "😡" if sentiment == "Negative"
            else "😐"
    })

# ---------------------------------------------------
# ANALYZE USER API
# ---------------------------------------------------

@app.route('/api/analyze-user', methods=['POST'])
def api_analyze_user():

    data = request.get_json() or {}

    username = data.get("username", "").strip()

    count = int(data.get("count", 5))

    if not username:

        return jsonify({
            "error": "No username provided."
        }), 400

    count = max(1, min(count, 10))

    tweets = []

    is_mock = True

    # -----------------------------------------------
    # TRY REAL TWITTER API
    # -----------------------------------------------

    if tweepy_client:

        try:

            clean_username = username.lstrip('@')

            user_response = tweepy_client.get_user(
                username=clean_username
            )

            if user_response.data:

                user_id = user_response.data.id

                tweets_response = tweepy_client.get_users_tweets(
                    id=user_id,
                    max_results=count,
                    tweet_fields=["created_at"]
                )

                if tweets_response.data:

                    is_mock = False

                    for t in tweets_response.data:

                        tweets.append({

                            "text": t.text,

                            "created_at":
                                t.created_at.strftime(
                                    "%Y-%m-%dT%H:%M:%S.000Z"
                                )
                                if t.created_at
                                else datetime.utcnow().strftime(
                                    "%Y-%m-%dT%H:%M:%S.000Z"
                                )
                        })

        except Exception as e:

            print(f"Twitter fetch failed: {e}")

    # -----------------------------------------------
    # FALLBACK TO MOCK DATA
    # -----------------------------------------------

    if not tweets:

        tweets = generate_mock_tweets(
            username,
            count
        )

        is_mock = True

    # -----------------------------------------------
    # ANALYZE TWEETS
    # -----------------------------------------------

    analyzed_tweets = []

    pos_count = 0
    neg_count = 0
    neu_count = 0

    for t in tweets:

        sentiment = predict_sentiment(t["text"])

        if sentiment == "Positive":

            pos_count += 1
            emoji = "😊"

        elif sentiment == "Negative":

            neg_count += 1
            emoji = "😡"

        else:

            neu_count += 1
            emoji = "😐"

        analyzed_tweets.append({

            "text": t["text"],

            "created_at": t["created_at"],

            "sentiment": sentiment,

            "emoji": emoji
        })

    total = len(analyzed_tweets)

    summary = {

        "total": total,

        "positive": pos_count,

        "negative": neg_count,

        "neutral": neu_count
    }

    return jsonify({

        "username": username,

        "count": count,

        "is_mock": is_mock,

        "tweets": analyzed_tweets,

        "summary": summary
    })

# ---------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------

@app.route('/health')
def health():

    return jsonify({
        "status": "running"
    })

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

if __name__ == '__main__':

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host='0.0.0.0',
        port=port
    )
