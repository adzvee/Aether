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
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/get_recommendations", json=payload)
        end_time = time.time()

        if response.status_code == 200:
            data = response.json()
            duration = round(end_time - start_time, 2)
            print(f"Response Time: {duration}s")
            print(f"QUOTE: \"{data.get('quote')}\"")
            print(f"AUTHOR: {data.get('author')}")
            print("ACTIVITIES:")
            for act in data.get('activities', []):
                print(f"  - {act['title']} [{act.get('type')}]")

            # Validation Check
            if data.get('author') and data.get('quote') and data.get('author') in data.get('quote'):
                print("WARNING: Author name detected inside the quote string!")

        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")


# Tests Suite

scenarios = [
    ("Drained", "Finals week is crushing me."),
    ("Nervous", "Interviewing for an internship in 10 minutes."),
    ("Overwhelmed", "I have 5 assignments due and my room is a mess."),
    ("Sad", "Feeling a bit lonely tonight."),
    ("Excited", "I just finished my first full-stack app!")
]

print("Starting Stress Test for Ollama Backend...")

for mood, note in scenarios:
    test_mood(mood, note)
    # Small gap to let the CPU breathe between generations
    time.sleep(1)

print("\nAll tests complete.")
