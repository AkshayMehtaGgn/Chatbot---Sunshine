from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import difflib
from datetime import datetime, timedelta
import requests
import os

app = Flask(__name__)
CORS(app)

# Load FAQs once
with open("faq.json", encoding="utf-8") as f:
    faqs = json.load(f)

# Google Apps Script Webhook
GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbwQtCehOyyyoMb8HX8vIp5P7HjyZo9n7Ma7xKiIu_fe2IZlzmRcigi4Nilbr2nTt--BDQ/exec"

# Timezone formatting for IST
def current_ist_timestamp():
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist_now.strftime("%Y-%m-%d %H:%M:%S")

# Best matching FAQ answer
def get_answer(user_question):
    user_question = user_question.strip().lower()
    questions = [faq["question"].strip().lower() for faq in faqs]
    closest = difflib.get_close_matches(user_question, questions, n=1, cutoff=0.5)
    if closest:
        match = closest[0]
        for faq in faqs:
            if faq["question"].strip().lower() == match:
                return faq["answer"]

    suggestions = difflib.get_close_matches(user_question, questions, n=3, cutoff=0.3)
    if suggestions:
        suggestion_text = "\n".join([f"- {s}" for s in suggestions])
    else:
        suggestion_text = "\n".join([f"- {faq['question']}" for faq in faqs[:3]])
    return (
        "🤖 I'm not sure how to answer that. Could you try rephrasing?\n"
        "Here are some things you can ask:\n" + suggestion_text
    )

# IP & location resolution
def get_user_ip_and_location(req):
    ip_address = req.headers.get('X-Forwarded-For', req.remote_addr or 'Unknown')
    location = "Unknown"
    try:
        geo_req = requests.get(f'https://ipapi.co/{ip_address}/json/')
        geo_data = geo_req.json()
        city = geo_data.get("city", "")
        region = geo_data.get("region", "")
        country = geo_data.get("country_name", "")
        location = f"{city}, {region}, {country}".strip(', ')
    except Exception as e:
        print("🌐 IP/Location error:", e)
    return ip_address, location

# POST to Google Sheet
def log_to_google_sheet(payload):
    try:
        response = requests.post(GOOGLE_SHEET_WEBHOOK, json=payload)
        print("🟢 Logged:", response.status_code, response.text)
    except Exception as e:
        print("❌ Google Sheets logging failed:", e)

# Default route for Render iframe
@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>FAQ Chatbot</title>
        <style>
            body { font-family: Arial; text-align: center; padding-top: 80px; }
            h1 { color: #0073aa; }
        </style>
    </head>
    <body>
        <h1>🤖 FAQ Chatbot is Running</h1>
        <p>You can integrate this into your site using an iframe or widget.</p>
    </body>
    </html>
    """)

# POST endpoint to get answer
@app.route('/get_answer', methods=['POST'])
def get_bot_answer():
    data = request.get_json()
    question = data.get("question", "").strip()
    name = data.get("name", "Unknown")
    contact = data.get("contact", "Unknown")
    email = data.get("email", "Unknown")

    if not question:
        return jsonify({"answer": "❗Please enter a valid question to get help."})

    answer = get_answer(question)
    ip, location = get_user_ip_and_location(request)
    timestamp = current_ist_timestamp()

    log_data = {
        "timestamp": timestamp,
        "name": name,
        "contact": contact,
        "email": email,
        "question": question,
        "answer": answer,
        "ip_address": ip,
        "location": location
    }

    log_to_google_sheet(log_data)
    return jsonify({"answer": answer})

# Run locally
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
