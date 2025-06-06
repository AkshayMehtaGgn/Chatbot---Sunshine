from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import difflib
from datetime import datetime


app = Flask(__name__)
CORS(app)

# Load FAQs from faq.json
with open("faq.json", encoding="utf-8") as f:
    faqs = json.load(f)

def get_answer(user_question):
    user_question = user_question.strip().lower()
    all_questions = [faq["question"].strip().lower() for faq in faqs]

    # Fuzzy match
    closest = difflib.get_close_matches(user_question, all_questions, n=1, cutoff=0.5)

    if closest:
        matched_q = closest[0]
        for faq in faqs:
            if faq["question"].strip().lower() == matched_q:
                return faq["answer"]

    # Fallback message with suggested questions
    suggestions = "\n".join(["- " + faq["question"] for faq in faqs[:3]])  # Top 3 suggestions
    return (
        "🤖 I'm not sure how to answer that. Could you try rephrasing?\n"
        "Here are some things you can ask:\n" + suggestions
    )

GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbwQtCehOyyyoMb8HX8vIp5P7HjyZo9n7Ma7xKiIu_fe2IZlzmRcigi4Nilbr2nTt--BDQ/exec"

@app.route('/get_answer', methods=['POST'])
def get_answer():
    data = request.get_json()
    user_question = data.get('question')
    name = data.get('name', 'Unknown')
    contact = data.get('contact', 'Unknown')
    email = data.get('email', 'Unknown')


    answer = get_answer(user_question)

    # Log the user info and question to a file
    try:
        requests.post(GOOGLE_SHEET_WEBHOOK, json={
            'name': name,
            'contact': contact,
            'email': email,
            'question': question,
            'answer': answer
        })
    except Exception as e:
        print("Logging to Google Sheets failed:", e)

    return jsonify({'answer': answer})

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
