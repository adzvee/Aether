import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from google import genai  # Modern library
from google.genai import types

load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///deerhacks.db')
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

# Modern Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

system_instruction = """You are a warm, supportive wellness companion for students.

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

import time


@app.route('/api/get_recommendations', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    mood = data.get('mood', 'Okay')
    note = data.get('note', '')

    # This is the prompt that tells Gemini the context
    user_prompt = f"The user is feeling: {mood}. Personal note: {note if note else 'No note provided.'}"

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json"
                )
            )

            response_data = json.loads(response.text)

            # Keep your 'music_suggestion' flag logic so frontend knows to show music icons
            for activity in response_data.get('activities', []):
                title_lower = activity.get('title', '').lower()
                if any(word in title_lower for word in ["music", "playlist", "listen"]):
                    activity['type'] = "music_suggestion"
                else:
                    activity['type'] = "standard"

            return jsonify(response_data), 200

        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"Rate limited. Retrying in 2 seconds... (Attempt {attempt + 1})")
                time.sleep(2)
                continue

            print(f"!!! DEBUG ERROR: {e}")
            return jsonify({"error": "The AI is a bit overwhelmed right now. Please try again in a few seconds."}), 500


@app.route('/api/logs', methods=['POST'])
def save_mood_log():
    """Initial log when a user picks a mood and writes a note."""
    data = request.get_json()
    if not data or 'mood_before' not in data:
        return jsonify({"error": "Initial mood is required"}), 400

    new_log = MoodLog(
        mood_before=data.get('mood_before'),
        note=data.get('note', '')
    )
    db.session.add(new_log)
    db.session.commit()
    return jsonify({"message": "Log saved!", "id": new_log.id}), 201


@app.route('/api/logs/<int:log_id>', methods=['PATCH'])
def update_mood_log(log_id):
    """Updates the log with the 'mood_after' once they finish an activity."""
    data = request.get_json()
    log_entry = MoodLog.query.get_or_404(log_id)

    if 'mood_after' in data:
        log_entry.mood_after = data.get('mood_after')
        db.session.commit()

    return jsonify({"message": "Log updated", "log": {
        "id": log_entry.id,
        "mood_after": log_entry.mood_after
    }}), 200


@app.route('/api/history', methods=['GET'])
def get_history():
    """Returns all past moods for the history chart/list."""
    logs = MoodLog.query.order_by(MoodLog.timestamp.desc()).all()
    return jsonify([{
        "id": log.id,
        "mood_before": log.mood_before,
        "mood_after": log.mood_after,
        "note": log.note,
        "timestamp": log.timestamp.isoformat()
    } for log in logs]), 200

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
