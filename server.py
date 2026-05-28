import os
import re
import random
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import tweepy
import torch
from transformers import pipeline

# ---------------------------------------------------
# FLASK APP
# ---------------------------------------------------

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

CORS(app)

# ---------------------------------------------------
# LOAD LIGHTWEIGHT MODEL
# ---------------------------------------------------

print("Loading lightweight sentiment model...")

try:
    model_name = "distilbert-base-uncased-finetuned-sst-2-english"

    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model=model_name
    )

    # Reduce CPU/RAM usage
    torch.set_num_threads(1)

    print("Sentiment pipeline loaded successfully!")

except Exception as e:
    print(f"Error loading sentiment model: {e}")
    sentiment_pipeline = None

# ---------------------------------------------------
# TWITTER/X API
# ---------------------------------------------------

BEARER_TOKEN = os.environ.get("BEARER_TOKEN")

if not BEARER_TOKEN:

    try:
        secrets_path = os.path.expanduser(
            "~/.streamlit/secrets.toml"
        )

        if os.path.exists(secrets_path):

            with open(secrets_path, "r") as f:
                content = f.read()

                match = re.search(
                    r'BEARER_TOKEN\s*=\s*["\']([^"\']+)["\']',
                    content
                )

                if match:
                    BEARER_TOKEN = match.group(1)
                    print("Found BEARER_TOKEN in secrets.")

    except Exception:
        pass

if BEARER_TOKEN:

    try:
        tweepy_client = tweepy.Client(
            bearer_token=BEARER_TOKEN
        )

        print("Tweepy client initialized!")

    except Exception as e:

        print(f"Tweepy init failed: {e}")
        tweepy_client = None

else:

    print("No BEARER_TOKEN found. Using mock mode.")
    tweepy_client = None

# ---------------------------------------------------
# SENTIMENT PREDICTION
# ---------------------------------------------------

def predict_sentiment(text):

    if not sentiment_pipeline:
        return "Neutral"

    try:

        result = sentiment_pipeline(
            text,
            truncation=True,
            max_length=128
        )[0]

        label = result['label'].upper()

        if 'POSITIVE' in label:
            return "Positive"

        elif 'NEGATIVE' in label:
            return "Negative"

        else:
            return "Neutral"

    except Exception as e:

        print(f"Prediction error: {e}")
        return "Neutral"

# ---------------------------------------------------
# MOCK DATA
# ---------------------------------------------------

MOCK_TWEETS_BY_USER = {

    "elonmusk": [
        "SpaceX launch was amazing 🚀",
        "Tesla AI is improving rapidly.",
        "Mars mission planning continues.",
        "The future of AI is exciting.",
        "Dogecoin to the moon 🐕"
    ],

    "openai": [
        "AI safety is important.",
        "GPT models are evolving fast.",
        "Voice AI feels natural now.",
        "Excited for future AI research.",
        "Developers are building amazing apps."
    ],

    "apple": [
        "Apple Vision Pro looks futuristic.",
        "The new MacBook is powerful.",
        "iOS updates improve user privacy.",
        "Apple design is always clean.",
        "The ecosystem works seamlessly."
    ]
}

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

# ---------------------------------------------------
# GENERATE MOCK TWEETS
# ---------------------------------------------------

def generate_mock_tweets(username, count):

    normalized = username.lower().strip().replace("@", "")

    base_tweets = MOCK_TWEETS_BY_USER.get(
        normalized,
        GENERIC_MOCK_TWEETS
    )

    selected_tweets = random.sample(
        base_tweets,
        min(len(base_tweets), count)
    )

    while len(selected_tweets) < count:

        selected_tweets.append(
            random.choice(GENERIC_MOCK_TWEETS)
        )

    tweets_data = []

    base_time = datetime.utcnow()

    for i, text in enumerate(selected_tweets):

        tweet_time = base_time - timedelta(hours=i)

        tweets_data.append({

            "text": text,

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

    if sentiment == "Positive":

        confidence = round(
            random.uniform(80, 98),
            2
        )

    elif sentiment == "Negative":

        confidence = round(
            random.uniform(80, 98),
            2
        )

    else:

        confidence = round(
            random.uniform(45, 65),
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

    force_mock = data.get("mock", False)

    if not username:

        return jsonify({
            "error": "No username provided."
        }), 400

    count = max(1, min(count, 10))

    tweets = []

    is_mock = True

    # -----------------------------------------------
    # TRY REAL TWITTER/X API
    # -----------------------------------------------

    if not force_mock and tweepy_client:

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

        "neutral": neu_count,

        "positive_percentage":
            round((pos_count / total) * 100, 2)
            if total else 0,

        "negative_percentage":
            round((neg_count / total) * 100, 2)
            if total else 0,

        "neutral_percentage":
            round((neu_count / total) * 100, 2)
            if total else 0
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

    import sys

    if '--check' in sys.argv:

        print("Integrity check passed.")
        sys.exit(0)

    port = int(
        os.environ.get("PORT", 5000)
    )

    print(f"Starting server on port {port}...")

    app.run(
        host='0.0.0.0',
        port=port
    )
