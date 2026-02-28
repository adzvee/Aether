import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000/api"

def test_mood(mood, note):
    print(f"\n--- Testing Mood: {mood} ---")
    payload = {
        "mood": mood,
        "note": note
    }

    try:
        response = requests.post(f"{BASE_URL}/get_recommendations", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"QUOTE: \"{data['quote']}\" - {data['author']}")
            print("ACTIVITIES:")
            for act in data['activities']:
                print(f"- {act['title']} (Type: {act.get('type')})")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

# --- Patient Test Scenarios ---

# Scenario A
test_mood("Drained", "Stayed up until 3am studying for my midterm.")

# Wait for the Free Tier quota to breathe
print("\n[Cooldown] Waiting 35 seconds for API quota to reset...")
time.sleep(35)

# Scenario B
test_mood("Nervous", "I have a big presentation today.")
