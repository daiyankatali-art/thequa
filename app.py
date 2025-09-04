from flask import Flask, jsonify, render_template, request
from google import genai
import pprint
import json
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")

# global variable to hold questions list
questions_list = ""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    email = request.form.get("email")
    topic = request.form.get("topic")
    amount = request.form.get("amount")
    
    client = genai.Client(api_key=API_KEY)
    
    prompt = f"""
    Generate {amount} short, clear,simple and concise essay-type questions along with their answers (1–2 sentences each) on the topic: {topic}. do number them.
    I want the response in this structure [
    {{"question": "Generated question 1?",  "answer": "Answer 1"}},
    {{"question": "Generated question 2?", "answer": "Answer 2"}},
    {{"question": "Generated question 3?", "answer": "Answer 3"}}
]
    I don't want it to have ```json I just want the json
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    global questions_list
    questions_list = json.loads(response.text)
    print(questions_list)
    # answers
    return render_template('question.html', questions=questions_list)

@app.route('/submit-answers', methods=['POST'])
def Result():
    global questions_list
    
    client = genai.Client(api_key=API_KEY)
    user_answer = request.form.to_dict()
    print("user answer -> ",user_answer)
    
    ana_prompt = f"""
    You are an expert evaluator. Analyze each user answer against the correct answer and provide detailed feedback with scoring.

    QUESTIONS AND ANSWERS: {questions_list}
    USER ANSWERS: {user_answer}

    For each question, provide:
    1. A score out of 10 (10 = perfect match, 0 = completely wrong)
    2. Detailed analysis explaining:
       - What the user got right
       - What the user missed or got wrong
       - How close their answer was to the correct answer
       - Specific suggestions for improvement

    Scoring criteria:
    - 9-10: Excellent - Covers all key points accurately
    - 7-8: Good - Covers most key points with minor gaps
    - 5-6: Fair - Some correct elements but missing important details
    - 3-4: Poor - Few correct elements, major gaps or errors
    - 0-2: Very Poor - Mostly incorrect or completely off-topic

    Return the data in this EXACT JSON format:
    [
        {{
            "question": "Original question text",
            "answer": "Correct answer",
            "user_answer": "User's actual answer",
            "score": 8,
            "analysis": "Detailed analysis: You correctly identified [specific points]. However, you missed [specific points]. Your answer shows [level of understanding]. To improve: [specific suggestions]. Score: 8/10 - Good understanding with room for improvement."
        }},
        {{
            "question": "Original question text",
            "answer": "Correct answer", 
            "user_answer": "User's actual answer",
            "score": 6,
            "analysis": "Detailed analysis with score explanation..."
        }}
    ]

    Make sure each analysis is personalized, constructive, and includes the score with explanation. Do not include ```json in your response.
    """
    
    print("======================= AFTER ANSWERING =======================")
    print(f"{questions_list}")
    
    print("\n\n\n\n")
    print("======================= AI ANALYSIS =======================")
    
    # get question with answers and analysis
    response_ana = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=ana_prompt
    )
    
    ana = json.loads(response_ana.text)
    print(ana)
    
    return render_template('result.html', ana=ana)

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)