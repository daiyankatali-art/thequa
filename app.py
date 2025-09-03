from flask import Flask, jsonify, render_template, request
from google import genai
import json

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')



@app.route('/generate', methods=['POST'])
def generate():
    email = request.form.get("email")
    topic = request.form.get("topic")
    amount = request.form.get("amount")


    
    client = genai.Client(api_key="AIzaSyBs7iJzEPSqKnF3ut_qEiqeRmdmfg8z_mA")


    prompt = f"""
    Generate {amount} short, clear,simple and concise essay-type questions along with their answers (1–2 sentences each) on the topic: {topic}. do number them.
    I want the response in this structure
[
    {{"question": "Generated question 1?", "answer": "Answer 1"}},
    {{"question": "Generated question 2?", "answer": "Answer 2"}},
    {{"question": "Generated question 3?", "answer": "Answer 3"}}
]
    I don't want it to have ```json I just want the json
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    
    return render_template('question.html', questions=json.loads(response.text))

@app.route('/submit-answers', methods=['POST'])
def Result():
    feedback=request.form.get("answer")
    return render_template('result.html')



if __name__ == '__main__':
    app.run(debug=True)