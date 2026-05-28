# AI Twitter/X Sentiment Analyzer

A modern, responsive web application designed to analyze the emotional sentiment of manual text and X (Twitter) timelines using state-of-the-art Deep Learning and Natural Language Processing.

---

## 🚀 Key Features

*   **Direct Statement Classifier**: Instantly run deep learning predictions on any custom statement, comment, or paragraph.
*   **Timeline Sentiment Explorer**: Fetch and evaluate the average sentiment trajectory and trends of public posts for any X (Twitter) profile.
*   **Simulated Demo Mode**: Features a realistic mock fallback mechanism that simulates X profile analysis when X API credentials are not set.
*   **Interactive Analytics Dashboard**: Beautiful visualization metrics summarizing sentiment percentages (Positive, Neutral, Negative) and total counts.
*   **Glassmorphic Design UI**: Stunning, modern, responsive user interface featuring micro-animations, color-coded sentiment indicators, and custom fonts.

---

## 🛠️ Technology Stack

*   **Frontend**: HTML5, Vanilla CSS3, JavaScript (ES6+), FontAwesome Icons, Google Fonts (Poppins).
*   **Backend Server**: Flask, Flask-CORS, Tweepy (X API Integration).
*   **AI Model Engine**: Hugging Face `transformers` pipeline utilizing **`cardiffnlp/twitter-roberta-base-sentiment-latest`** (a RoBERTa-based transformer model trained on over 124 million tweets and optimized for 3-class sentiment prediction).
*   **Machine Learning Runtime**: PyTorch (CPU-optimized).

---

## 📦 Installation & Setup

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### 2. Clone and Setup Environment
Navigate to the project root directory and install the required dependencies:
```bash
pip install -r requirements.txt
```
*Note: To minimize installation size, you can install the CPU-only version of PyTorch:*
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers
```

### 3. Run the Application
Start the Flask development server:
```bash
python server.py
```

Open your browser and navigate to:
```
http://localhost:5000
```

---

## 🧪 Verification and Integrity
You can run an integrity and dependency check using:
```bash
python server.py --check
```
This verifies that all deep learning weights, configurations, tokenizers, and dependencies are correctly set up and ready to run.
