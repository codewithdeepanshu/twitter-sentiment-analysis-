import os
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

print("Lightweight sentiment app started!")

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

        print(f"Twitter client error: {e}")
        tweepy_client = None

else:

    print("No BEARER_TOKEN found. Using mock mode.")
    tweepy_client = None

# ---------------------------------------------------
# SIMPLE SENTIMENT ANALYSIS
# ---------------------------------------------------

POSITIVE_WORDS = [
    "love",
    "great",
    "awesome",
    "good",
    "happy",
    "excellent",
    "amazing",
    "beautiful",
    "best",
    "fantastic",
    "cool",
    "nice"
]

NEGATIVE_WORDS = [
    "bad",
    "terrible",
    "awful",
    "hate",
    "worst",
    "sad",
    "angry",
    "disappointed",
    "broken",
    "useless",
    "horrible"
]

def predict_sentiment(text):

    text = text.lower()

    positive_score = sum(
        word in text for word in POSITIVE_WORDS
    )

    negative_score = sum(
        word in text for word in NEGATIVE_WORDS
    )

    if positive_score > negative_score:
        return "Positive"

    elif negative_score > positive_score:
        return "Negative"

    else:
        return "Neutral"

# ---------------------------------------------------
# MOCK TWEETS
# ---------------------------------------------------

MOCK_TWEETS = [

    "I love this new technology!",
    "Today is an amazing day!",
    "This product is terrible.",
    "The weather looks beautiful.",
    "Traffic today is horrible.",
    "Coding is really fun.",
    "Customer support disappointed me.",
    "This movie is awesome!",
    "I feel happy today.",
    "The service was bad."
]

def generate_mock_tweets(count):

    tweets = []

    base_time = datetime.utcnow()

    for i in range(count):

        tweet_time = base_time - timedelta(hours=i)

        tweets.append({

            "text": random.choice(MOCK_TWEETS),

            "created_at": tweet_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        })

    return tweets

# ---------------------------------------------------
# HOME ROUTE
# ---------------------------------------------------

@app.route('/')
def home():

    return render_template('index.html')

# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------

@app.route('/dashboard')
def dashboard():

    return render_template('dashboard.html')

# ---------------------------------------------------
# ANALYZE TEXT
# ---------------------------------------------------

@app.route('/api/analyze-text', methods=['POST'])
def analyze_text():

    data = request.get_json()

    text = data.get("text", "").strip()

    if not text:

        return jsonify({
            "error": "No text provided"
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
# ANALYZE USER
# ---------------------------------------------------

@app.route('/api/analyze-user', methods=['POST'])
def analyze_user():

    data = request.get_json()

    username = data.get("username", "").strip()

    count = int(data.get("count", 5))

    if not username:

        return jsonify({
            "error": "No username provided"
        }), 400

    count = max(1, min(count, 10))

    tweets = []

    is_mock = True

    # -----------------------------------------------
    # TRY REAL TWITTER API
    # -----------------------------------------------

    if tweepy_client:

        try:

            clean_username = username.replace("@", "")

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

                    for tweet in tweets_response.data:

                        tweets.append({

                            "text": tweet.text,

                            "created_at":
                                tweet.created_at.strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                                if tweet.created_at
                                else datetime.utcnow().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                        })

        except Exception as e:

            print(f"Twitter fetch failed: {e}")

    # -----------------------------------------------
    # FALLBACK TO MOCK DATA
    # -----------------------------------------------

    if not tweets:

        tweets = generate_mock_tweets(count)

        is_mock = True

    # -----------------------------------------------
    # ANALYZE TWEETS
    # -----------------------------------------------

    analyzed_tweets = []

    positive = 0
    negative = 0
    neutral = 0

    for tweet in tweets:

        sentiment = predict_sentiment(
            tweet["text"]
        )

        if sentiment == "Positive":

            positive += 1
            emoji = "😊"

        elif sentiment == "Negative":

            negative += 1
            emoji = "😡"

        else:

            neutral += 1
            emoji = "😐"

        analyzed_tweets.append({

            "text": tweet["text"],

            "created_at": tweet["created_at"],

            "sentiment": sentiment,

            "emoji": emoji
        })

    total = len(analyzed_tweets)

    summary = {

        "total": total,

        "positive": positive,

        "negative": negative,

        "neutral": neutral
    }

    return jsonify({

        "username": username,

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
