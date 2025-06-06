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

@app.route('/get_answer', methods=['POST'])
def get_bot_answer():
    data = request.get_json()
    user_question = data.get('question', '')
    name = data.get('name', 'Anonymous')
    email = data.get('email', 'Not Provided')
    phone = data.get('phone', 'Not Provided')

    answer = get_answer(user_question)

    # Log the user info and question to a file
    with open("chat_logs.txt", "a", encoding='utf-8') as log_file:
        log_entry = f"{datetime.now()} | Name: {name} | Email: {email} | Phone: {phone} | Question: {user_question} | Answer: {answer}\n"
        log_file.write(log_entry)

    return jsonify({'answer': answer})

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
