from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import difflib
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# Load FAQs once from local faq.json
with open("faq.json", encoding="utf-8") as f:
    faqs = json.load(f)

# Google Apps Script Webhook
GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbwQtCehOyyyoMb8HX8vIp5P7HjyZo9n7Ma7xKiIu_fe2IZlzmRcigi4Nilbr2nTt--BDQ/exec"

# Answer retrieval via fuzzy matching
def get_answer(user_question):
    user_question = user_question.strip().lower()
    all_questions = [faq["question"].strip().lower() for faq in faqs]
    closest = difflib.get_close_matches(user_question, all_questions, n=1, cutoff=0.5)

    if closest:
        matched_q = closest[0]
        for faq in faqs:
            if faq["question"].strip().lower() == matched_q:
                return faq["answer"]
    
    suggestions = "\n".join(["- " + faq["question"] for faq in faqs[:3]])
    return (
        "🤖 I'm not sure how to answer that. Could you try rephrasing?\n"
        "Here are some things you can ask:\n" + suggestions
    )

# User IP and Location lookup
def get_user_ip_and_location(req):
    ip_address = req.remote_addr or 'Unknown'
    location = 'Unknown'
    try:
        geo_req = requests.get(f'https://ipapi.co/{ip_address}/json/')
        geo_data = geo_req.json()
        city = geo_data.get("city", "")
        region = geo_data.get("region", "")
        country = geo_data.get("country_name", "")
        location = f"{city}, {region}, {country}".strip(', ')
    except Exception as e:
        print("🌐 Failed to fetch IP/location:", e)
    return ip_address, location

# POST logs to Google Sheet
def log_to_google_sheet(payload):
    try:
        response = requests.post(GOOGLE_SHEET_WEBHOOK, json=payload)
        print("🟢 Posted to Google Sheet:", response.status_code)
        print("📄 Response:", response.text)
    except Exception as e:
        print("❌ Logging to Google Sheets failed:", e)

@app.route('/get_answer', methods=['POST'])
def get_bot_answer():
    data = request.get_json()
    user_question = data.get('question', '').strip()
    name = data.get('name', 'Unknown')
    contact = data.get('contact', 'Unknown')
    email = data.get('email', 'Unknown')
    feedback = data.get('feedback', '')  # Optional Yes/No feedback

    if not user_question:
        return jsonify({'answer': "❗Please ask a valid question."})

    answer = get_answer(user_question)
    ip_address, location = get_user_ip_and_location(request)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        'timestamp': timestamp,
        'name': name,
        'contact': contact,
        'email': email,
        'question': user_question,
        'answer': answer,
        'ip_address': ip_address,
        'location': location,
        'feedback': feedback
    }

    log_to_google_sheet(payload)
    return jsonify({'answer': answer})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
