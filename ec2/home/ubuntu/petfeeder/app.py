from flask import Flask, request, jsonify
from flask_cors import CORS
import pyrebase
import datetime
from collections import defaultdict
import json
from openai import OpenAI

app = Flask(__name__)
CORS(app) #Allows React to securely fetch data from this API/app is the backend server


# FIREBASE CONFIGURATION

firebaseConfig = {
  //
}

#connection to firebase
firebase = pyrebase.initialize_app(firebaseConfig)
#creates the database object
db = firebase.database()

# Initialize the OpenAI client pointing to GitHub
ai_client = OpenAI(
)
  //
)

@app.route('/api/ai-consultant', methods=['POST'])
def ai_consultant():
    data = request.json
    pet_type = data.get('pet_type', 'cat')
    breed = data.get('breed', 'Unknown')
    age = data.get('age', '1')
    current_weight = data.get('weight', '4')

    # This prompt forces the model to return a structured JSON response
    prompt = f"""
    You are an expert veterinary nutritionist. Provide a meal plan for a {age}-year-old {breed} {pet_t>
    Return ONLY a raw JSON object with these exact keys (do not include markdown formatting, markdown >
    {{
      "recommended_grams_per_day": integer,
      "number_of_feedings": integer,
      "health_warning": "Provide a HIGHLY SPECIFIC genetic or breed-unique health warning for a {breed>
    }}
    """

    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        # Parse the response to ensure it's valid JSON before handing it to the frontend
        ai_data = json.loads(response.choices[0].message.content.strip())

        # save pet profile to firebase
        db.child("feeder_status").child("pet_profile").set(ai_data)

        return jsonify(ai_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

the endpoint where we get data from, created by us
@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        # Fetch Data
        live_data = db.child("feeder_status").child("live").get().val() or {"food_percentage": 0.0, "p>
        schedule_node = db.child("feeder_status").child("schedule").get().val()
        schedule_list = [v for k, v in schedule_node.items()] if schedule_node else []
        history_node = db.child("feeder_status").child("history").get().val()
        pet_profile = db.child("feeder_status").child("pet_profile").get().val()

        history_list = []
        inventory_labels, inventory_data = [], []
        daily_visits = defaultdict(int)

        if history_node:
            for key, value in history_node.items():
                history_list.append(value)
                timestamp = value.get("timestamp", str(datetime.datetime.now()))
                date_str, time_str = timestamp[:10], timestamp[11:16]

                inventory_labels.append(f"{date_str} {time_str}")
                inventory_data.append(value.get("food_grams", 0))

                if value.get("pet_detected") == True:
                    daily_visits[date_str] += 1

            history_list.reverse()

        return jsonify({
            "live": live_data,
            "schedule": schedule_list,
            "history": history_list[:10],
            "charts": {
                "inventory": {"labels": inventory_labels[-20:], "data": inventory_data[-20:]},
                "visits": {"labels": list(daily_visits.keys())[-7:], "data": list(daily_visits.values(>
            },
            "pet_profile": pet_profile
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

