from flask import Flask, jsonify, render_template, request
from flask import Flask, jsonify, request
from google import genai
import json

app = Flask(__name__)

def parse_json_to_dict(json_string):
    """
    Parses a JSON string and returns a Python dictionary.
    """
    try:
        data_dict = json.loads(json_string)
        return data_dict
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    email = request.form.get("email")
    topic = request.form.get("topic")
    amount = request.form.get("amount")

    # genai.configure("AIzaSyBs7iJzEPSqKnF3ut_qEiqeRmdmfg8z_mA")

    # model = genai.GenerativeModel("gemini-1.5-flash")
    client = genai.Client(api_key="AIzaSyBs7iJzEPSqKnF3ut_qEiqeRmdmfg8z_mA")


    prompt = f"""
    Generate {amount} short, clear,simple and concise essay-type questions along with their answers (1–2 sentences each) on the topic: {topic}. do not number them.
    I want the response in this structure
    {{
        1: {{ 
            "question": "safsdfsdaf",
            "answer": "sdfsdfsdf"
        }},
    }}

    I don't want it to have ```json I just want the json
    """

    # response = model.generate_content([prompt])
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    data = parse_json_to_dict(response.text)
    results = [{"answer":item["answer"],"question":item["question"]} for item in data.values()]
    return jsonify(results)
    # print(data_dict.keys())
    # return response.text

if __name__ == '__main__':
    app.run(debug=True)