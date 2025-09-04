from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Global variable to hold questions list
questions_list = ""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    email = request.form.get("email")
    topic = request.form.get("topic")
    amount = request.form.get("amount")
    uploaded_file = request.files.get('file')  # May be None or empty

    # ❌ If neither topic nor file is provided
    if not topic and (not uploaded_file or uploaded_file.filename == ''):
        return "❌ Please provide either a topic or upload a PDF file.", 400

    client = genai.Client(api_key=API_KEY)

    # 📄 If file uploaded and not empty, read its bytes
    file_bytes = None
    file_part = None
    if uploaded_file and uploaded_file.filename != '':
        file_bytes = uploaded_file.read()
        if len(file_bytes) == 0:
            return "❌ Uploaded file is empty", 400
        file_part = types.Part.from_bytes(data=file_bytes, mime_type='application/pdf')

    # 🧠 Build the prompt
    prompt = f"""
You are a smart assistant. Based on the input below, generate exactly {amount} short, clear, simple essay-type questions with 1–2 sentence answers.

"""

    if topic:
        prompt += f"TOPIC: {topic}\n"

    prompt += """
Output ONLY in this JSON format:
[
  { "question": "Question 1?", "answer": "Answer 1" },
  { "question": "Question 2?", "answer": "Answer 2" }
]

Do NOT include markdown, code blocks, or explanations — just the raw JSON.
"""

    # 📦 Build contents for Gemini
    contents = []
    if file_part:
        contents.append(file_part)
    contents.append(prompt)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents
        )
        raw_text = response.text
        print("📥 Gemini response:", raw_text)

        global questions_list
        questions_list = json.loads(raw_text)

        return render_template("question.html", questions=questions_list)

    except json.JSONDecodeError as e:
        print("❌ JSON parsing error:", e)
        return "⚠️ AI response was not valid JSON.", 500
    except Exception as e:
        print("❌ Error:", e)
        return f"⚠️ An error occurred: {str(e)}", 500

@app.route('/submit-answers', methods=['POST'])
def Result():
    global questions_list

    client = genai.Client(api_key=API_KEY)
    user_answer = request.form.to_dict()
    print("📝 User answers:", user_answer)

    ana_prompt = f"""
You are an expert evaluator. Analyze each user answer against the correct answer and provide detailed feedback with scoring.

QUESTIONS AND ANSWERS: {questions_list}
USER ANSWERS: {user_answer}

For each question, provide:
1. A score out of 10
2. A detailed analysis including:
   - What the user got right
   - What was missing or incorrect
   - Suggestions for improvement

Use this EXACT format:
[
  {{
    "question": "Question?",
    "answer": "Correct Answer",
    "user_answer": "User's Answer",
    "score": 8,
    "analysis": "Feedback with scoring explanation"
  }},
  ...
]

Do NOT include code blocks or markdown.
"""

    try:
        response_ana = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=ana_prompt
        )

        ana = json.loads(response_ana.text)
        print("📊 Evaluation result:", ana)

        return render_template("result.html", ana=ana)

    except json.JSONDecodeError as e:
        print("❌ JSON parsing error:", e)
        return "⚠️ AI analysis was not valid JSON.", 500
    except Exception as e:
        print("❌ Error:", e)
        return f"⚠️ An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
