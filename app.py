from flask import Flask, request, jsonify
from flask_cors import CORS
import json, difflib, requests, logging, os

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# Load and preprocess FAQs
with open("faq.json", encoding="utf-8") as f:
    faqs = json.load(f)

faq_map = {faq["question"].strip().lower(): faq["answer"] for faq in faqs}

GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbw.../exec"

def get_answer(user_question):
    user_question = user_question.strip().lower()
    closest = difflib.get_close_matches(user_question, faq_map.keys(), n=1, cutoff=0.5)

    if closest:
        return faq_map[closest[0]]

    suggestions = "\n".join(f"- {q}" for q in list(faq_map.keys())[:3])
    return (
        "🤖 I'm not sure how to answer that. Could you try rephrasing?\n"
        "Here are some things you can ask:\n" + suggestions
    )

def get_client_ip(req):
    return (req.headers.get('X-Forwarded-For') or req.remote_addr or '0.0.0.0').split(',')[0]

def get_location_from_ip(ip):
    try:
        res = requests.get(f"https://ipapi.co/{ip}/json/")
        data = res.json()
        return f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country_name', '')}"
    except Exception as e:
        logging.warning("IP lookup failed: %s", e)
        return "Unknown"

@app.route('/get_answer', methods=['POST'])
def get_bot_answer():
    data = request.get_json()
    user_question = data.get('question', '')
    name = data.get('name', 'Unknown')
    contact = data.get('contact', 'Unknown')
    email = data.get('email', 'Unknown')

    answer = get_answer(user_question)
    ip_address = get_client_ip(request)
    location = get_location_from_ip(ip_address)

    payload = {
        'name': name,
        'contact': contact,
        'email': email,
        'question': user_question,
        'answer': answer,
        'ip_address': ip_address,
        'location': location
    }

    try:
        response = requests.post(GOOGLE_SHEET_WEBHOOK, json=payload)
        logging.info("Posted to Google Sheet: %s", response.status_code)
    except Exception as e:
        logging.error("Logging to Google Sheets failed: %s", e)

    return jsonify({'answer': answer})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
