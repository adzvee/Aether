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
            print(f"Response Time: {round(end_time - start_time, 2)}s")
            print(f"QUOTE: \"{data['quote']}\" - {data['author']}")
            print("ACTIVITIES:")
            for act in data['activities']:
                # Verify that our 'music_suggestion' logic is working locally
                print(f"- {act['title']} (Type: {act.get('type')})")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

# Scenario A
test_mood("Drained", "Stayed up until 3am studying for my midterm.")

print("\n[Local Gap] Waiting 2 seconds...")
time.sleep(2)

# Scenario B
test_mood("Nervous", "I have a big presentation today.")
