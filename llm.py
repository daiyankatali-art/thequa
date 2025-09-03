from google import genai
import json
client = genai.Client(api_key="AIzaSyBs7iJzEPSqKnF3ut_qEiqeRmdmfg8z_mA")
import pprint

amount=5
topic="history"

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

# get question from ai
questions = ""
# get question with answers
response = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=prompt
    )
for chunk in response:
    questions += chunk.text
    print(chunk.text, end='', flush=True)

# convert list to dict
questions_list = json.loads(questions)

print("\n\n\n\n")
# print(questions_list)
# print(type(questions))\\\\
print("======================= BEFORE ANSWERING =======================")

pprint.pprint(f"yooo questions list first here -> \n{questions_list}")

for i,q in enumerate(questions_list):
    # print(q)
    print(f"""
Question {i+1}: {q['question']}
""")
    answer = input("Your answer: ")
    questions_list[i]['user_answer'] = answer

print("\n\n")
print("======================= AFTER ANSWERING =======================")
pprint.pprint(f"yooo questions list first here -> {questions_list}")


ana_prompt = f"""
ANANYLISE THE FOLLOWING QUESTIONS AND ANSWERS WITH USERS RESPONSE INSIDE OF THE DATA AND THEN GIVE THE USER YOUR FEEDBACK/ANALYISES ON THEIR REPONSE FOR EACH QUESTION 
{questions_list}
ADD YOUR ANALYSIS BACK TO EACH QUESTION DICT IN THE DATA.
[
{{"question": "Generated question 1?", "answer": "Answer 1", "user_answer": "USER_ANSWER_HERE", "analysis": "YOUR_ANAL"}},
{{"question": "Generated question 1?", "answer": "Answer 2", "user_answer": "USER_ANSWER_HERE", "analysis": "YOUR_ANAL"}},
{{"question": "Generated question 1?", "answer": "Answer 3", "user_answer": "USER_ANSWER_HERE", "analysis": "YOUR_ANAL"}},
]
I don't want it to have ```json I just want the json
"""

print("\n\n\n\n")
print("======================= AI ANALYSIS =======================")
# get question from ai
analysis = ""
# get question with answers
response_ana = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=ana_prompt
    )
for chunk in response_ana:
    analysis += chunk.text
    print(chunk.text, end='', flush=True)
ana = json.loads(analysis)
print(ana)

""" for i in range(1, 6):
    # response = client.models.generate_content(
    #     model="gemini-2.5-flash",
    #     contents=prompt
    # )
    # print(response.text)
    # print("============================================\n\n")
    response = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=prompt
    )
    for chunk in response:
        print(chunk.text, end='', flush=True)
    print("============================================\n\n") """