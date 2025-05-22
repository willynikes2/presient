import os
import sys
import datetime
import requests

# Add backend to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Simulated event payload
payload = {
    "user_id": "user_001",          # Match ID from your seed
    "sensor_id": "sensor_alpha",    # Simulated sensor ID
    "confidence": 0.93,             # High-confidence match
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
}

# Send the POST request to local API
url = "http://localhost:8000/presence/event"

print(f"➡️  Sending presence event to {url}")
response = requests.post(url, json=payload)

if response.ok:
    print("✅ Presence event accepted:", response.json())
else:
    print("❌ Error:", response.status_code, response.text)
