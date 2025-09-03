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
    I want the response in this structure
[
    {{"question": "Generated question 1?",
 "answer": "Answer 1"}},
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
    ANANYLISE  THE {questions_list} YOU PROVIDED EARLIER WITH THE {user_answer} INSIDE OF THE DATA AND THEN GIVE THE USER YOUR FEEDBACK/ANALYISES ON THEIR REPONSE FOR EACH QUESTION
    BASED ON HOW CLOSE THE USER IS TO THE ANSWER(THE AI) PROVIDED.
    ADD YOUR ANALYSIS BACK TO EACH QUESTION DICT IN THE DATA.
    [
    {{"question": "Generated question 1?", "answer": "Answer 1", "user_answer": "USER_ANSWER_HERE", "analysis": "YOUR_ANALYSIS"}},
    {{"question": "Generated question 1?", "answer": "Answer 2", "user_answer": "USER_ANSWER_HERE", "analysis": "YOUR_ANALYSIS"}},
    {{"question": "Generated question 1?", "answer": "Answer 3", "user_answer": "USER_ANSWER_HERE", "analysis": "YOUR_ANALYSIS"}},
    ]
    I don't want it to have ```json I just want the json
    """

    

    print("======================= AFTER ANSWERING =======================")
    print(f"{questions_list}")


    
    print("\n\n\n\n")
    print("======================= AI ANALYSIS =======================")
    # get question from ai
    analysis = ""
    # get question with answers
    response_ana = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=ana_prompt
    )
    
    ana = json.loads(response_ana.text)
    #print(ana)

    return render_template('result.html', ana=ana)

if __name__ == '__main__':
    app.run(debug=True)