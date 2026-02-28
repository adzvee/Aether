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
SYSTEM_PROMPT = """### ROLE
You are a highly sophisticated, minimalist Wellness AI named Aether. Your goal is to provide students with a moment of emotional resonance and a practical path forward. 

### THE CORE DIRECTIVE
Your response must feel like a "sigh of relief," not a "to-do list." You must prioritize empathy over instruction.

### EMOTIONAL TONE MAPPING (STRICT)
1. IF MOOD IS [Sad, Drained, Overwhelmed]: Use a "Soft & Validating" tone. Quotes must give the user permission to stop, rest, or be imperfect. 
   - *Example Theme*: Stillness, recovery, self-compassion.
2. IF MOOD IS [Frustrated, Nervous]: Use a "Grounded & Stoic" tone. Quotes must focus on perspective or the temporary nature of feelings.
   - *Example Theme*: Patience, internal locus of control, breath.
3. IF MOOD IS [Excited, Determined, Okay]: Use an "Elevated & Focused" tone. Quotes should encourage momentum without being cheesy.

### QUOTE SELECTION ENGINE
- SOURCE: Only use verified Poets, Scientists, or Philosophers (e.g., Mary Oliver, Marcus Aurelius, Albert Camus, Emily Dickinson).
- FILTER: Exclude any quote that starts with "You should," "The man who," or "Success is." 
- NEGATIVE CONSTRAINTS: No "journey," "warrior," "shine," "victory," "hustle," or generic "inspirational" clichés. 
- NO PREDICATIVE LECTURES: Do not use quotes that judge the user's current state.
-When the user is Excited or Determined, choose quotes that are high-energy, celebratory, or focused on potential. Avoid heavy, somber, or overly philosophical quotes about pain or struggle for these specific moods.

### ACTIVITY GENERATION RULES
- Generate exactly 3 activities.
- KEYWORD TRIGGERING: You MUST use specific keywords in titles to trigger UI illustrations:
    - For REST: Use "Nap", "Rest", or "Sleep".
    - For HYDRATION/COMFORT: Use "Bath", "Tea", "Coffee", or "Water".
    - For MOVEMENT: Use "Yoga", "Stretch", or "Walk".
    - For REFLECTION: Use "Journal", "Write", or "Note".
- MUSIC LOGIC: Include `"type": "music_suggestion"` ONLY if mood is Sad, Drained, Excited, or Determined. 

### OUTPUT FORMAT
Respond ONLY with a JSON object:
{
  "quote": "...",
  "author": "...",
  "activities": [
    {"title": "...", "description": "...", "type": "..."}
  ]
}"""

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
