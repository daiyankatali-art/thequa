from flask import Flask, jsonify, render_template, request, redirect, url_for, render_template_string
from flask_mail import Mail, Message
from google import genai
from google.genai import types
import json
import os
import requests
import re
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")

mail = Mail(app)

# Global variable
questions_list = []


def extract_text_from_url(url):
    """Extract text from a webpage."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html_content = response.text

        # Remove scripts and styles
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text).strip()

        # Replace entities
        text = (text.replace('&nbsp;', ' ')
                    .replace('&amp;', '&')
                    .replace('&lt;', '<')
                    .replace('&gt;', '>')
                    .replace('&quot;', '"')
                    .replace('&#39;', "'"))

        return text[:5000] if len(text) > 5000 else text
    except Exception as e:
        raise Exception(f"Error fetching/processing URL: {str(e)}")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    email = request.form.get("email")
    topic = request.form.get("topic", "").strip()
    amount = request.form.get("amount")
    url = request.form.get("url", "").strip()
    uploaded_file = request.files.get('file')

    has_topic = bool(topic)
    has_url = bool(url)
    has_file = bool(uploaded_file and uploaded_file.filename.strip())

    if not has_topic and not has_url and not has_file:
        return "❌ Please provide at least one of: a topic, a URL, or upload a file.", 400

    client = genai.Client(api_key=API_KEY)
    url_content, file_part = "", None

    if has_url:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        url_content = extract_text_from_url(url)

    if has_file:
        file_bytes = uploaded_file.read()
        if len(file_bytes) == 0:
            return "❌ Uploaded file is empty", 400
        file_part = types.Part.from_bytes(data=file_bytes, mime_type='application/pdf')

    # Strict prompt for Gemini
    prompt = f"""
You are a question generator.

TASK: Create exactly {amount} short, clear essay-type questions with 1–2 sentence answers.

RULES:
- Output must be valid JSON only.
- No markdown, no code blocks, no explanations, no extra text.
- Use only this format:

[
  {{"question": "Question 1?", "answer": "Answer 1"}},
  {{"question": "Question 2?", "answer": "Answer 2"}}
]
"""
    if has_topic:
        prompt += f"\nTOPIC: {topic}"
    if has_url and url_content:
        prompt += f"\nURL CONTENT: {url_content}"
    if has_file:
        prompt += f"\nFILE: {uploaded_file.filename} (content processed)"

    contents = []
    if file_part:
        contents.append(file_part)
    contents.append(prompt)

    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=contents)
        raw_text = response.text
        global questions_list
        questions_list = json.loads(raw_text)

        return render_template("question.html", questions=questions_list, email=email)

    except json.JSONDecodeError:
        return "⚠️ AI response was not valid JSON.", 500
    except Exception as e:
        return f"⚠️ Error: {str(e)}", 500


@app.route('/submit-answers', methods=['POST'])
def result():
    global questions_list
    client = genai.Client(api_key=API_KEY)
    user_email = request.form.get("email")
    user_answers = {k: v for k, v in request.form.items() if k != "email"}

    # Fixed strict evaluation prompt with escaped braces
    ana_prompt = f"""
You are a strict but helpful evaluator for student quiz answers.

TASK: For each question:
1. Compare the user's answer with the correct answer.
2. Give a score between 0–10.
   - 10 = fully correct
   - 7–9 = mostly correct but with small mistakes
   - 4–6 = partially correct, missing key details
   - 1–3 = very weak, vague, or incomplete
   - 0 = irrelevant, blank, or nonsensical
3. Write clear, constructive feedback that:
   - Explains why the score was given
   - Highlights what the user got right (if anything)
   - Explains what was missing or incorrect
   - Suggests how the user could improve their answer next time

RULES:
- Output must be valid JSON only.
- No markdown, no code blocks, no explanations outside the JSON.
- Use exactly this structure:

[
  {{{{
    "question": "Question?",
    "answer": "Correct Answer",
    "user_answer": "User's Answer",
    "score": 8,
    "analysis": "Your answer mentioned memory management, which is correct, but you missed the part about process scheduling. To improve, explain how the OS handles both resources and processes."
  }}}}
]

QUESTIONS: {questions_list}
ANSWERS: {user_answers}
"""

    try:
        response_ana = client.models.generate_content(model="gemini-2.5-flash", contents=ana_prompt)
        ana = json.loads(response_ana.text)

        return render_template("result.html", ana=ana, email=user_email)

    except json.JSONDecodeError:
        return "⚠️ AI analysis was not valid JSON.", 500
    except Exception as e:
        return f"⚠️ Error: {str(e)}", 500


@app.route('/send-results', methods=['POST'])
def send_results():
    email = request.form.get("email")
    results_json = request.form.get("results")

    if not email or not results_json:
        return "⚠️ Missing email or results data.", 400

    try:
        ana = json.loads(results_json)
        msg = Message(subject="Your Quiz Results", recipients=[email])
    
        # Render HTML email similar to result.html
        html_content = render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Quiz Results</title>
    <style>
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #f9f9f9; margin:0; padding:0; }
        .container { max-width: 700px; margin: 30px auto; background: #ffffff; padding: 25px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 25px; }
        .header h1 { color: #333333; font-size: 28px; margin-bottom: 5px; }
        .header p { color: #666666; font-size: 16px; margin-top: 0; }
        .question-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 20px; background: #fdfdfd; }
        .question-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .question-number { font-weight: bold; color: #555555; }
        .question-text { font-weight: 600; color: #222222; flex: 1; margin-left: 10px; }
        .score-badge { padding: 4px 10px; border-radius: 12px; background: #28a745; color: #ffffff; font-weight: bold; font-size: 0.9em; }
        .answer-section { margin-bottom: 10px; }
        .section-title { font-weight: 700; color: #333333; margin-bottom: 4px; }
        .answer-text { background: #f4f4f4; padding: 8px 12px; border-radius: 6px; font-size: 14px; color: #555555; }
        @media only screen and (max-width: 600px) {
            .container { padding: 15px; }
            .question-header { flex-direction: column; align-items: flex-start; }
            .question-text { margin-left: 0; margin-top: 5px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Quiz Results</h1>
            <p>Review your answers and detailed feedback below.</p>
        </div>
        {% for a in ana %}
        <div class="question-card">
            <div class="question-header">
                <div class="question-number">{{ loop.index }}</div>
                <div class="question-text">{{ a.question }}</div>
                <div class="score-badge">{{ a.score }}/10</div>
            </div>
            <div class="answer-section">
                <div class="section-title">Correct Answer</div>
                <div class="answer-text">{{ a.answer }}</div>
            </div>
            <div class="answer-section">
                <div class="section-title">Your Answer</div>
                <div class="answer-text">{{ a.user_answer }}</div>
            </div>
            <div class="answer-section">
                <div class="section-title">Analysis & Feedback</div>
                <div class="answer-text">{{ a.analysis }}</div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
""", ana=ana)

        msg.html = html_content  # Set HTML content for email
        mail.send(msg)
        print(f"✅ Results sent to {email}")
        return html_content

    except json.JSONDecodeError:
        return "⚠️ Results data was not valid JSON.", 500
    except Exception as e:
        print("❌ Error sending email:", e)
        return "⚠️ Failed to send results", 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
