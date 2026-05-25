from flask import Flask, render_template, request, redirect, url_for
import pyrebase
import datetime

app = Flask(__name__)

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

@app.route('/')
def index():
    try:
        # 1. Get the Live Status
        live_data = db.child("feeder_status").child("live").get().val()
        
        # 2. Get the latest 10 History logs
        history_node = db.child("feeder_status").child("history").order_by_key().limit_to_last(10).get().val()
        
        # Convert history dictionary to a list and reverse it so newest is on top
        history_list = []
        if history_node:
            for key, value in history_node.items():
                history_list.append(value)
            history_list.reverse()
	# 3. Get Schedule
        schedule_node = db.child("feeder_status").child("schedule").get().val()
        schedule_list = [v for k, v in schedule_node.items()] if schedule_node else []
            
    except Exception as e:
        print(f"Database error: {e}")
        live_data = None
        history_list = []

    # Send data to the HTML page
    return render_template('index.html', live=live_data, history=history_list, schedule=schedule_list)

@app.route('/dispense', methods=['POST'])
def dispense():
    try:
        # Create a command payload with a timestamp
        command_data = {
            "action": "dispense",
            "trigger": True,
            "timestamp": str(datetime.datetime.now())
        }
        # Write it to a new "commands" node in Firebase
        db.child("commands").set(command_data)
        print("[WEB] Dispense command sent to Firebase!")
    except Exception as e:
        print(f"Error sending command: {e}")

    # Refresh the page immediately
    return redirect(url_for('index'))

@app.route('/set_schedule', methods=['POST'])
def set_schedule():
    try:
        # Get the time from the HTML form (Format will be "HH:MM")
        feed_time = request.form.get('feed_time')
        if feed_time:
            # Push the new time to Firebase
            db.child("feeder_status").child("schedule").push(feed_time)
            print(f"[WEB] Scheduled new feeding time: {feed_time}")
    except Exception as e:
        print(f"Error setting schedule: {e}")
        
    return redirect(url_for('index'))



if __name__ == '__main__':
    # Run on all public IP addresses on port 5000
    app.run(host='0.0.0.0', port=5000)
