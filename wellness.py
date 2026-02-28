import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import ollama

load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///aether.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class MoodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mood_before = db.Column(db.String(50), nullable=False)
    mood_after = db.Column(db.String(50), nullable=True)
    note = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

SYSTEM_PROMPT = """You are a warm, supportive wellness companion for students.
The user will provide their current mood and an optional personal note.
Respond with ONLY valid JSON in this exact format:
{
  "quote": "A short grounded quote from a real person. No clichés.",
  "author": "Author Name",
  "activities": [
    {"title": "Activity Title", "description": "One sentence description"}
  ]
}
Rules:
- Quote must be from a real author, artist, or philosopher. No clichés like warrior or shine.
- Suggest exactly 3 activities that are specific, actionable, and realistic for a student right now.
- Only suggest music as an activity for: Sad, Drained, Excited, Determined. Never for Overwhelmed or Frustrated or Nervous or Okay.
- If a personal note was provided, reference it subtly.
- Tone must be gentle, human, and encouraging. Never clinical or generic."""

@app.route('/api/get_recommendations', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    mood = data.get('mood', 'Okay')
    note = data.get('note', '')

    user_prompt = f"The user is feeling: {mood}. Personal note: {note if note else 'No note provided.'}"

    try:
        # Calling Ollama locally with llama3.2
        response = ollama.chat(
            model='llama3.2',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            format='json' # This tells Llama to output structured JSON
        )


        response_text = response['message']['content']
        response_data = json.loads(response_text)

        for activity in response_data.get('activities', []):
            title_lower = activity.get('title', '').lower()
            if any(word in title_lower for word in ["music", "playlist", "listen"]):
                activity['type'] = "music_suggestion"
            else:
                activity['type'] = "standard"

        return jsonify(response_data), 200

    except Exception as e:
        print(f"!!! OLLAMA ERROR: {e}")
        return jsonify({"error": "Local AI is taking a nap. Make sure Ollama is running!"}), 500


@app.route('/api/logs', methods=['POST'])
def save_mood_log():
    data = request.get_json()
    if not data or 'mood_before' not in data:
        return jsonify({"error": "Initial mood is required"}), 400
    new_log = MoodLog(mood_before=data.get('mood_before'), note=data.get('note', ''))
    db.session.add(new_log)
    db.session.commit()
    return jsonify({"message": "Log saved!", "id": new_log.id}), 201

@app.route('/api/logs/<int:log_id>', methods=['PATCH'])
def update_mood_log(log_id):
    data = request.get_json()
    log_entry = MoodLog.query.get_or_404(log_id)
    if 'mood_after' in data:
        log_entry.mood_after = data.get('mood_after')
        db.session.commit()
    return jsonify({"message": "Log updated"}), 200

@app.route('/api/history', methods=['GET'])
def get_history():
    logs = MoodLog.query.order_by(MoodLog.timestamp.desc()).all()
    return jsonify([{
        "id": log.id, "mood_before": log.mood_before,
        "mood_after": log.mood_after, "note": log.note,
        "timestamp": log.timestamp.isoformat()
    } for log in logs]), 200

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
