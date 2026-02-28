import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask import render_template
import ollama

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
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

# UPDATED: Added strict formatting rules
SYSTEM_PROMPT = """You are a minimalist, empathetic wellness coach for students. 
You must match the quote's THEME to the user's specific NOTE and MOOD.

Respond with ONLY valid JSON in this exact format:
{
  "quote": "The quote text only",
  "author": "Author Name",
  "activities": [
    {"title": "Activity Title", "description": "One sentence description"}
  ]
}

EXAMPLES OF CORRECT THEME MATCHING:
- Note: "Busload of work/busy" -> Theme: Focus/Patience -> Quote: "One by one, all things are done."
- Note: "Failed/Mistake" -> Theme: Growth -> Quote: "Mistakes are the portals of discovery."
- Note: "Tired/Burnt out" -> Theme: Permission to rest -> Quote: "Rest is not idleness."

STRICT NEGATIVE CONSTRAINTS:
1. NEVER use Zig Ziglar or the quote: "You don't have to be great to start..."
2. NEVER use: "Be the change you wish to see" or "Well-behaved women seldom make history."
3. NEVER use any quote containing the word "journey", "warrior", or "shine".
4. Use ONLY real philosophers, poets, or scientists. No generic "inspirational" clichés.

ACTIVITY RULES:
- Suggest exactly 3 activities that are specific and realistic for a student.
- Only suggest music for: Sad, Drained, Excited, Determined.
- NEVER suggest music for: Overwhelmed, Frustrated, Nervous, or Okay.
- Reference the user's personal note subtly in the descriptions."""

@app.route('/api/get_recommendations', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    mood = data.get('mood', 'Okay')
    note = data.get('note', '')

    # Adding a unique timestamp forces the AI to treat every request as brand new
    unique_seed = datetime.now().strftime("%H:%M:%S")
    user_prompt = f"Time: {unique_seed}. Mood: {mood}. Personal note: {note if note else 'No note provided.'}"

    try:
        # UPDATED: Added top_p and higher temperature for maximum variety
        response = ollama.chat(
            model='llama3.2',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            format='json',
            options={
                'temperature': 0.9,  # Increased for variety
                'top_p': 0.9,        # Encourages more diverse word choices
                'num_predict': 400
            }
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
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
