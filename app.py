from flask import Flask, render_template, request, redirect, url_for, session
from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # needed for session storage

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Global variable to hold questions list
questions_list = []

# ---------------------- HOME PAGE ----------------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------------------- GENERATE QUESTIONS ----------------------
@app.route('/generate', methods=['POST'])
def generate():
    email = request.form.get("email")
    topic = request.form.get("topic")
    amount = request.form.get("amount")
    uploaded_file = request.files.get('file')

    # Save email in session to use later
    session['user_email'] = email

    client = genai.Client(api_key=API_KEY)

    # Handle uploaded file
    file_part = None
    if uploaded_file and uploaded_file.filename != '':
        file_bytes = uploaded_file.read()
        if len(file_bytes) == 0:
            return "❌ Uploaded file is empty", 400
        file_part = types.Part.from_bytes(data=file_bytes, mime_type='application/pdf')

    # Build prompt
    prompt = f"""
You are a smart assistant. Generate exactly {amount} short essay-type questions with 1-2 sentence answers.
"""
    if topic:
        prompt += f"TOPIC: {topic}\n"

    prompt += """
Output ONLY in JSON format:
[
  {"question": "Question 1?", "answer": "Answer 1"},
  {"question": "Question 2?", "answer": "Answer 2"}
]
Do NOT include markdown or code blocks.
"""

    # Build contents
    contents = [prompt]
    if file_part:
        contents.insert(0, file_part)

    # Generate questions using Gemini
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents
        )
        raw_text = response.text.strip()
        if not raw_text:
            return "⚠️ AI returned empty response. Try again.", 500

        global questions_list
        questions_list = json.loads(raw_text)
        return render_template("question.html", questions=questions_list)

    except json.JSONDecodeError as e:
        print("❌ JSONDecodeError:", e)
        print("RAW RESPONSE:", response.text)
        return "⚠️ AI response was not valid JSON.", 500
    except Exception as e:
        print("❌ Error:", e)
        return f"⚠️ An error occurred: {str(e)}", 500

# ---------------------- SUBMIT ANSWERS ----------------------
@app.route('/submit-answers', methods=['POST'])
def Result():
    global questions_list
    client = genai.Client(api_key=API_KEY)
    user_answers = request.form.to_dict()

    ana_prompt = f"""
You are an expert evaluator. Analyze each user answer against the correct answer.

QUESTIONS: {questions_list}
USER ANSWERS: {user_answers}

Return a JSON array like:
[
  {{
    "question": "Original question",
    "answer": "Correct answer",
    "user_answer": "User answer",
    "score": 8,
    "analysis": "Detailed feedback"
  }},
  ...
]
Do NOT include markdown or code blocks.
"""

    try:
        response_ana = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=ana_prompt
        )
        raw_text = response_ana.text.strip()
        if not raw_text:
            return "⚠️ AI returned empty analysis. Try again.", 500

        ana = json.loads(raw_text)
        session['analysis'] = ana  # save for emailing

        return render_template("result.html", ana=ana)

    except json.JSONDecodeError as e:
        print("❌ JSONDecodeError:", e)
        print("RAW RESPONSE:", response_ana.text)
        return "⚠️ AI analysis was not valid JSON.", 500
    except Exception as e:
        print("❌ Error:", e)
        return f"⚠️ An error occurred: {str(e)}", 500

# ---------------------- SEND EMAIL ----------------------
@app.route('/send-email' , methods=['POST'])
def send_email():
    user_email = session.get("user_email")
    ana = session.get("analysis")

    if not user_email or not ana:
        return "❌ No email or results available to send.", 400

    # Build email content
    results_text = "Your Quiz Results\n\n"
    for q in ana:
        results_text += f"Question: {q['question']}\n"
        results_text += f"Correct Answer: {q['answer']}\n"
        results_text += f"Your Answer: {q['user_answer']}\n"
        results_text += f"Analysis: {q['analysis']}\n\n"

    try:
        sender_email = os.getenv("SENDER_EMAIL")
        app_password = os.getenv("APP_PASSWORD")

        msg = EmailMessage()
        msg.set_content(results_text)
        msg['Subject'] = "Your Quiz Results"
        msg['From'] = sender_email
        msg['To'] = user_email

        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)

        message = f"✅ Results have been sent to {user_email}"


    except Exception as e:
         message = f"❌ Failed to send email: {str(e)}"


    return render_template("email_sent.html", message=message)

# ---------------------- MAIN ----------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
