#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, jsonify
import requests
import os
from dotenv import load_dotenv

# Load your HA_TOKEN and HA_URL from your .env file
load_dotenv()

app = Flask(__name__)

HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")
HEADERS = {"Authorization": f"Bearer {HA_TOKEN}"}

def get_ha_data(entity_id):
    try:
        r = requests.get(HA_URL + entity_id, headers=HEADERS, timeout=5)
        return r.json()
    except Exception as e:
        return {"state": "error", "attributes": {}}

@app.route('/divoom/data')
def divoom_data():
    # 1. Fetch Windows (Numeric)
    window_state = get_ha_data("number.open_doors_and_windows")['state']
    
    # 2. Fetch Dog Status (String)
    dog_time = get_ha_data("input_datetime.time_dog_was_outside")['state']
    
    # 3. Fetch Next Calendar Event (String)
    cal = get_ha_data("calendar.arnon_shimoni_gmail_com")
    event_name = cal.get('attributes', {}).get('message', 'No Event')

    # Return exactly what Divoom expects
    return jsonify({
        "windows": int(float(window_state)) if window_state.replace('.','',1).isdigit() else 0,
        "dog_status": f"{dog_time}",
        "event": event_name  # Truncate to fit Divoom screen
    })

if __name__ == '__main__':
    # '0.0.0.0' makes it accessible on your local network
    app.run(host='0.0.0.0', port=5000)
