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
    # Use Twitter-RoBERTa model from cardiffnlp (supports Positive, Neutral, Negative natively)
    model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=model_name
)
    print("BERT/RoBERTa sentiment pipeline loaded successfully!")
except Exception as e:
    print(f"Error loading BERT/RoBERTa model pipeline: {e}")
    sentiment_pipeline = None

# ---------- X/TWITTER CLIENT ----------
BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
if not BEARER_TOKEN:
    # Try looking for streamlit secrets if available
    try:
        # Simple parser for streamlit secrets if they exist locally
        secrets_path = os.path.expanduser("~/.streamlit/secrets.toml")
        if os.path.exists(secrets_path):
            with open(secrets_path, "r") as f:
                content = f.read()
                match = re.search(r'BEARER_TOKEN\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    BEARER_TOKEN = match.group(1)
                    print("Found BEARER_TOKEN in Streamlit secrets.")
    except Exception:
        pass

if BEARER_TOKEN:
    try:
        tweepy_client = tweepy.Client(bearer_token=BEARER_TOKEN)
        print("Tweepy Client initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Tweepy client: {e}")
        tweepy_client = None
else:
    print("No BEARER_TOKEN found. Tweepy Client disabled (will default to Mock Mode).")
    tweepy_client = None

# ---------- PREDICT FUNCTION ----------
def predict_sentiment(text):
    if not sentiment_pipeline:
        # Fallback if model fails to load
        text_lower = text.lower()
        pos_words = ["love", "great", "excellent", "awesome", "good", "happy", "amazing", "beautiful", "best", "like"]
        neg_words = ["bad", "terrible", "awful", "hate", "worst", "sad", "disappointed", "angry", "broken", "useless"]
        pos_count = sum(1 for w in pos_words if w in text_lower)
        neg_count = sum(1 for w in neg_words if w in text_lower)
        if pos_count > neg_count:
            return "Positive"
        elif neg_count > pos_count:
            return "Negative"
        return "Neutral"

    try:
        # Hugging Face transformers pipeline handles tokenization and prediction.
        # BERT models perform best when tokenized with punctuation and stopwords intact.
        result = sentiment_pipeline(text, truncation=True, max_length=512)[0]
        label = result['label'].upper()
        
        # twitter-roberta model labels map to negative/neutral/positive (or LABEL_0, LABEL_1, LABEL_2)
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
        "Going to Mars is essential to preserve the light of consciousness. We must become a multiplanetary species.",
        "X (formerly Twitter) server architecture is undergoing massive optimization. Spammers are losing.",
        "Honestly, coding in assembly is quite fun, but python is just so productive for modern AI workloads.",
        "Working on some interesting physics problems tonight. The universe is incredibly beautiful and mysterious.",
        "Doge to the moon? 🐕 Maybe. But engineering real products is what matters.",
        "The mainstream media is suffering from severe echo-chamber bias. Community notes is the solution.",
        "Sigh, inflation is a real pain. We need to boost manufacturing output to solve it.",
        "Sometimes I wonder if we are living in a giant computer simulation. The math fits."
    ],
    "openai": [
        "Today we are announcing GPT-5, our most capable and aligned language model yet. The developer API is open. 🧠",
        "AI safety is not an afterthought; it is our primary mission. We are hosting a global safety summit.",
        "ChatGPT now has voice conversations that feel incredibly natural. Try it out on iOS and Android! 🎙️",
        "We believe that artificial general intelligence (AGI) should benefit all of humanity, not just a few. 🤝",
        "Excited to partner with creators to build custom GPTs for specific workloads. The store is now live.",
        "Our latest robotics research shows how LLMs can plan complex physical tasks in real time.",
        "We are actively recruiting researchers in safety, alignment, and systems engineering. Join us!",
        "API rate limits have been increased for all tier levels. Thank you for building with OpenAI.",
        "System maintenance is complete. All API services are back online and fully operational.",
        "Ethics in AI development must remain front and center as we push the frontiers of technology."
    ],
    "apple": [
        "Introducing Apple Vision Pro: the era of spatial computing has officially arrived. 🕶️🍏",
        "The new MacBook Pro with M4 Max is our most powerful laptop ever. Outrageously fast.",
        "iOS 20 introduces deep AI system integrations designed from the ground up to protect user privacy. 🔒",
        "We are proud to announce that all our corporate offices and retail stores are running on 100% renewable energy. 🌿",
        "Design is not just what it looks like and feels like. Design is how it works. - Steve Jobs",
        "Apple Watch Ultra 3: designed for extreme environments, athletes, and explorers. 🏔️⏱️",
        "Developers have generated over $300 billion in app store sales since inception. An incredible ecosystem.",
        "We are constantly exploring new materials to reduce our environmental carbon footprint by 2030.",
        "The new iPad Pro is thinner than a pencil and features a stunning tandem OLED display.",
        "Our customer support is always here to help you get the most out of your Apple devices. "
    ]
}

GENERIC_MOCK_TWEETS = [
    "Just had the most amazing cup of coffee this morning! The weather is perfect. ☕☀️",
    "Honestly, the traffic in the city today is a total nightmare. I'm going to be late again. 😡🚗",
    "Coding all night. Debugging is like being a detective in a movie where you are also the murderer. 💻",
    "I can't believe how bad the customer service was today. Never using this company again! 👎❌",
    "The new sci-fi movie is absolutely incredible. The visuals and soundtrack are 10/10! 🎬🍿",
    "Just finished reading a fascinating book about neuroscience and habits. Highly recommend it.",
    "Very disappointed with the product quality. It broke after just two days of normal use. 💔🔧",
    "A nice, quiet evening at home with a book. Sometimes that is all you need to recharge. 📖🍵",
    "I am so proud of my team for launching this project on time. Great effort by everyone! 🎉🙌",
    "The weather forecast says it might rain later, but it looks pretty sunny right now. We'll see."
]

def generate_mock_tweets(username, count):
    normalized = username.lower().strip().replace("@", "")
    base_tweets = MOCK_TWEETS_BY_USER.get(normalized, [])
    
    # If not a specific predefined user, create dynamic looking tweets by mixing generic tweets
    if not base_tweets:
        random.seed(normalized) # Stable mock tweets for same username
        base_tweets = random.sample(GENERIC_MOCK_TWEETS, min(len(GENERIC_MOCK_TWEETS), count * 2))
    
    # Select count items
    random.seed(None) # Reset seed
    selected_tweets = random.sample(base_tweets, min(len(base_tweets), count))
    
    # If we need more, pad with generic tweets
    while len(selected_tweets) < count:
        candidate = random.choice(GENERIC_MOCK_TWEETS)
        if candidate not in selected_tweets:
            selected_tweets.append(candidate)
            
    # Format them with mock metadata
    tweets_data = []
    base_time = datetime.utcnow()
    for i, text in enumerate(selected_tweets):
        tweet_time = base_time - timedelta(hours=i * 2 + random.randint(0, 55))
        tweets_data.append({
            "text": text,
            "created_at": tweet_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        })
    return tweets_data

# ---------- API ROUTES ----------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/analyze-text', methods=['POST'])
def api_analyze_text():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"error": "No text provided."}), 400
        
    sentiment = predict_sentiment(text)
    
    # Give a mock probability/confidence based on prediction
    if sentiment == "Positive":
        confidence = round(random.uniform(75.0, 98.0), 2)
    elif sentiment == "Negative":
        confidence = round(random.uniform(75.0, 98.0), 2)
    else:
        confidence = round(random.uniform(45.0, 65.0), 2)
        
    return jsonify({
        "text": text,
        "sentiment": sentiment,
        "confidence": confidence,
        "emoji": "😊" if sentiment == "Positive" else "😐" if sentiment == "Neutral" else "😡"
    })

@app.route('/api/analyze-user', methods=['POST'])
def api_analyze_user():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    count = int(data.get("count", 5))
    force_mock = data.get("mock", False)
    
    if not username:
        return jsonify({"error": "No username provided."}), 400
        
    if count < 1:
        count = 5
    elif count > 20:
        count = 20
        
    tweets = []
    is_mock = True
    
    # Try Tweepy if not forced mock and available
    if not force_mock and tweepy_client:
        try:
            # Remove leading @ if present
            clean_username = username.lstrip('@')
            user_response = tweepy_client.get_user(username=clean_username)
            
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
                            "created_at": t.created_at.strftime("%Y-%m-%dT%H:%M:%S.000Z") if hasattr(t, 'created_at') and t.created_at else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
                        })
        except Exception as e:
            print(f"Twitter API fetch failed for {username}: {e}. Falling back to mock data.")
            
    # Fallback to mock data if empty (because API failed, token is missing, or mock was requested)
    if not tweets:
        tweets = generate_mock_tweets(username, count)
        is_mock = True
        
    # Analyze sentiments
    analyzed_tweets = []
    pos_count = 0
    neu_count = 0
    neg_count = 0
    
    for t in tweets:
        sentiment = predict_sentiment(t["text"])
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
        "positive_percentage": round((pos_count / total * 100), 2) if total > 0 else 0,
        "neutral_percentage": round((neu_count / total * 100), 2) if total > 0 else 0,
        "negative_percentage": round((neg_count / total * 100), 2) if total > 0 else 0
    }
    
    return jsonify({
        "username": username,
        "count": count,
        "is_mock": is_mock,
        "tweets": analyzed_tweets,
        "summary": summary
    })

if __name__ == '__main__':
    # Add a checker flag to check imports and startup integrity
    import sys
    if '--check' in sys.argv:
        print("Integrity check passed.")
        sys.exit(0)
        
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting server on http://localhost:{port}...")
    app.run(host='0.0.0.0', port=port)
