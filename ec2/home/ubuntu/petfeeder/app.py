from flask import Flask, request, jsonify
from flask_cors import CORS
import pyrebase
import datetime
from collections import defaultdict

app = Flask(__name__)
CORS(app) # CRITICAL: Allows React to securely fetch data from this API

# ==========================================
# FIREBASE CONFIGURATION
# ==========================================
firebaseConfig = {
  "apiKey": "AIzaSyDMLnwwDZdFTaD-9KsOnZtUQaQjA9EWziI",
  "authDomain": "petfeeder-d4b6d.firebaseapp.com",
  "databaseURL": "https://petfeeder-d4b6d-default-rtdb.europe-west1.firebasedatabase.app",
  "projectId": "petfeeder-d4b6d",
  "storageBucket": "petfeeder-d4b6d.firebasestorage.app",
  "messagingSenderId": "995365531427",
  "appId": "1:995365531427:web:e12c8cc17c1f013a81a696"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        # Fetch Data
        live_data = db.child("feeder_status").child("live").get().val() or {"food_percentage": 0.0, "pet_detected": False}
        schedule_node = db.child("feeder_status").child("schedule").get().val()
        schedule_list = [v for k, v in schedule_node.items()] if schedule_node else []
        history_node = db.child("feeder_status").child("history").get().val()
        
        history_list = []
        inventory_labels, inventory_data = [], []
        daily_visits = defaultdict(int)

        if history_node:
            for key, value in history_node.items():
                history_list.append(value)
                timestamp = value.get("timestamp", str(datetime.datetime.now()))
                date_str, time_str = timestamp[:10], timestamp[11:16]
                
                inventory_labels.append(f"{date_str} {time_str}")
                inventory_data.append(value.get("food_percentage", 0))
                
                if value.get("pet_detected") == True:
                    daily_visits[date_str] += 1

            history_list.reverse()

        return jsonify({
            "live": live_data,
            "schedule": schedule_list,
            "history": history_list[:10],
            "charts": {
                "inventory": {"labels": inventory_labels[-20:], "data": inventory_data[-20:]},
                "visits": {"labels": list(daily_visits.keys())[-7:], "data": list(daily_visits.values())[-7:]}
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dispense', methods=['POST'])
def dispense():
    try:
        db.child("commands").set({
            "action": "dispense",
            "trigger": True,
            "timestamp": str(datetime.datetime.now())
        })
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedule', methods=['POST'])
def set_schedule():
    try:
        data = request.json
        feed_time = data.get('feed_time')
        if feed_time:
            db.child("feeder_status").child("schedule").push(feed_time)
            return jsonify({"status": "success"})
        return jsonify({"error": "No time provided"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
