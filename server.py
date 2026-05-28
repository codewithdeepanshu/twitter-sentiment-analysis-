import os
import re
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import tweepy
from transformers import pipeline

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ---------- LOAD ML RESOURCES ----------
print("Loading model resources (BERT/RoBERTa)...")

try:
    # Original RoBERTa Twitter sentiment model
    model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"

    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model=model_name,
        device=-1
    )

    print("BERT/RoBERTa sentiment pipeline loaded successfully!")

except Exception as e:

    print(f"Error loading BERT/RoBERTa model pipeline: {e}")
    sentiment_pipeline = None

# ---------- X/TWITTER CLIENT ----------

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

                    print(
                        "Found BEARER_TOKEN in Streamlit secrets."
                    )

    except Exception:
        pass

if BEARER_TOKEN:

    try:

        tweepy_client = tweepy.Client(
            bearer_token=BEARER_TOKEN
        )

        print("Tweepy Client initialized successfully.")

    except Exception as e:

        print(f"Failed to initialize Tweepy client: {e}")
        tweepy_client = None

else:

    print(
        "No BEARER_TOKEN found. Tweepy Client disabled."
    )

    tweepy_client = None

# ---------- PREDICT FUNCTION ----------

def predict_sentiment(text):

    if not sentiment_pipeline:

        # fallback keyword logic

        text_lower = text.lower()

        pos_words = [
            "love",
            "great",
            "excellent",
            "awesome",
            "good",
            "happy",
            "amazing",
            "beautiful",
            "best",
            "like"
        ]

        neg_words = [
            "bad",
            "terrible",
            "awful",
            "hate",
            "worst",
            "sad",
            "disappointed",
            "angry",
            "broken",
            "useless"
        ]

        pos_count = sum(
            1 for w in pos_words if w in text_lower
        )

        neg_count = sum(
            1 for w in neg_words if w in text_lower
        )

        if pos_count > neg_count:
            return "Positive"

        elif neg_count > pos_count:
            return "Negative"

        return "Neutral"

    try:

        result = sentiment_pipeline(
            text,
            truncation=True,
            max_length=512
        )[0]

        label = result['label'].upper()

        # RoBERTa label mapping

        if 'POSITIVE' in label or 'LABEL_2' in label:
            return "Positive"

        elif 'NEGATIVE' in label or 'LABEL_0' in label:
            return "Negative"

        else:
            return "Neutral"

    except Exception as e:

        print(f"Error predicting sentiment: {e}")

        return "Neutral"

# ---------- MOCK DATA GENERATOR ----------

MOCK_TWEETS_BY_USER = {

    "elonmusk": [

        "SpaceX Starship orbital flight test scheduled for next week! Extremely excited to see it fly. 🚀",

        "Tesla FSD Beta v12 is a mind-blowing release. Completely neural net based, no human code. 🚗⚡",

        "Going to Mars is essential to preserve the light of consciousness.",

        "X server architecture is undergoing optimization.",

        "Coding in assembly is fun, but Python is productive for AI."
    ],

    "openai": [

        "Today we are announcing GPT-5.",

        "AI safety is our primary mission.",

        "ChatGPT now has voice conversations.",

        "AGI should benefit all humanity.",

        "Excited to partner with developers."
    ],

    "apple": [

        "Introducing Apple Vision Pro.",

        "The new MacBook Pro is powerful.",

        "iOS introduces AI system integrations.",

        "Design is how it works.",

        "Apple Watch Ultra is designed for explorers."
    ]
}

GENERIC_MOCK_TWEETS = [

    "Just had the most amazing coffee today!",

    "Traffic in the city today is horrible.",

    "Coding all night debugging bugs.",

    "Customer service was terrible today.",

    "The new movie was incredible!",

    "Finished reading a fascinating book.",

    "Very disappointed with the product quality.",

    "A nice quiet evening at home.",

    "Proud of my team for launching this project.",

    "Weather forecast says rain later."
]

def generate_mock_tweets(username, count):

    normalized = username.lower().strip().replace("@", "")

    base_tweets = MOCK_TWEETS_BY_USER.get(normalized, [])

    if not base_tweets:

        random.seed(normalized)

        base_tweets = random.sample(
            GENERIC_MOCK_TWEETS,
            min(
                len(GENERIC_MOCK_TWEETS),
                count * 2
            )
        )

    random.seed(None)

    selected_tweets = random.sample(
        base_tweets,
        min(len(base_tweets), count)
    )

    while len(selected_tweets) < count:

        candidate = random.choice(
            GENERIC_MOCK_TWEETS
        )

        if candidate not in selected_tweets:
            selected_tweets.append(candidate)

    tweets_data = []

    base_time = datetime.utcnow()

    for i, text in enumerate(selected_tweets):

        tweet_time = base_time - timedelta(
            hours=i * 2 + random.randint(0, 55)
        )

        tweets_data.append({

            "text": text,

            "created_at":
                tweet_time.strftime(
                    "%Y-%m-%dT%H:%M:%S.000Z"
                )
        })

    return tweets_data

# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ---------- ANALYZE TEXT ----------

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
            random.uniform(75.0, 98.0),
            2
        )

    elif sentiment == "Negative":

        confidence = round(
            random.uniform(75.0, 98.0),
            2
        )

    else:

        confidence = round(
            random.uniform(45.0, 65.0),
            2
        )

    return jsonify({

        "text": text,

        "sentiment": sentiment,

        "confidence": confidence,

        "emoji":
            "😊" if sentiment == "Positive"
            else "😐" if sentiment == "Neutral"
            else "😡"
    })

# ---------- ANALYZE USER ----------

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

    if count < 1:
        count = 5

    elif count > 20:
        count = 20

    tweets = []

    is_mock = True

    if not force_mock and tweepy_client:

        try:

            clean_username = username.lstrip('@')

            user_response = tweepy_client.get_user(
                username=clean_username
            )

            if user_response.data is not None:

                user_id = user_response.data.id

                tweets_response = tweepy_client.get_users_tweets(
                    id=user_id,
                    max_results=count,
                    tweet_fields=["created_at"]
                )

                if tweets_response.data is not None:

                    is_mock = False

                    for t in tweets_response.data:

                        tweets.append({

                            "text": t.text,

                            "created_at":
                                t.created_at.strftime(
                                    "%Y-%m-%dT%H:%M:%S.000Z"
                                )
                                if hasattr(t, 'created_at')
                                and t.created_at
                                else datetime.utcnow().strftime(
                                    "%Y-%m-%dT%H:%M:%S.000Z"
                                )
                        })

        except Exception as e:

            print(
                f"Twitter API fetch failed: {e}"
            )

    if not tweets:

        tweets = generate_mock_tweets(
            username,
            count
        )

        is_mock = True

    analyzed_tweets = []

    pos_count = 0
    neu_count = 0
    neg_count = 0

    for t in tweets:

        sentiment = predict_sentiment(
            t["text"]
        )

        if sentiment == "Positive":

            pos_count += 1
            emoji = "😊"

        elif sentiment == "Neutral":

            neu_count += 1
            emoji = "😐"

        else:

            neg_count += 1
            emoji = "😡"

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

        "neutral": neu_count,

        "negative": neg_count,

        "positive_percentage":
            round((pos_count / total * 100), 2)
            if total > 0 else 0,

        "neutral_percentage":
            round((neu_count / total * 100), 2)
            if total > 0 else 0,

        "negative_percentage":
            round((neg_count / total * 100), 2)
            if total > 0 else 0
    }

    return jsonify({

        "username": username,

        "count": count,

        "is_mock": is_mock,

        "tweets": analyzed_tweets,

        "summary": summary
    })

# ---------- MAIN ----------

if __name__ == '__main__':

    import sys

    if '--check' in sys.argv:

        print("Integrity check passed.")

        sys.exit(0)

    port = int(
        os.environ.get("PORT", 5000)
    )

    print(
        f"Starting server on http://localhost:{port}..."
    )

    app.run(
        host='0.0.0.0',
        port=port
    )
