  GNU nano 8.7.1                                  bridge.py
import time
import json
import pyrebase
import datetime
import pytz
from awscrt import mqtt5
from awsiot import mqtt5_client_builder

# 1. FIREBASE CONFIGURATION

firebaseConfig = {
 //
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()


# 2. AWS IOT CONFIGURATION

ENDPOINT = //
CERT = /
KEY = //
TOPIC = "Test1"
COMMAND_TOPIC =//
CLIENT_ID = //

last_saved_food = None
DROP_THRESHOLD = 2.0

# 3. MESSAGE HANDLERS

def on_publish_received(publish_packet_data):
    """Handles incoming sensor data from AWS and pushes to Firebase"""
    global last_saved_food
    publish_packet = publish_packet_data.publish_packet
    payload = publish_packet.payload.decode('utf-8')

    try:
        sensor_data = json.loads(payload)
        current_food = sensor_data.get("food_percentage", 0.0)
        pet_here = sensor_data.get("pet_detected", False)

        db.child("feeder_status").child("live").set(sensor_data)

        should_save_to_history = False
        if pet_here:
            should_save_to_history = True
        elif last_saved_food is None:
            should_save_to_history = True
        elif abs(last_saved_food - current_food) >= DROP_THRESHOLD:
            should_save_to_history = True

        if should_save_to_history:
            sensor_data["timestamp"] = str(datetime.datetime.now())
            db.child("feeder_status").child("history").push(sensor_data)
            last_saved_food = current_food
            print("[FIREBASE] Live & History updated!")
        else:
            print("[FIREBASE] Live updated.")
    except Exception as e:
        print(f"Error processing AWS message: {e}")


def command_handler(message):
    """Listens to Firebase and pushes commands down to AWS"""
    try:
        # Check if the data is a valid command update
        if message["event"] in ["put", "patch"] and message["data"] is not None:
            data = message["data"]
            # If the user pressed the button, trigger is True
            if data.get("action") == "dispense" and data.get("trigger") == True:
                print("\n[WEB APP] Dispense button pressed! Forwarding to AWS...")

                # Send the command to AWS IoT
                payload = json.dumps({"feed_command": True})
                client.publish(mqtt5.PublishPacket(
                    topic=COMMAND_TOPIC,
                    payload=payload,
                    qos=mqtt5.QoS.AT_LEAST_ONCE
                ))

                # Reset the trigger in Firebase so it doesn't fire twice
                db.child("commands").update({"trigger": False})
    except Exception as e:
        print(f"Error handling Firebase command: {e}")
# 4. MAIN LOOP

if __name__ == '__main__':
    print("Starting 2-Way Cloud Bridge...")

    client = mqtt5_client_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=CERT,
        pri_key_filepath=KEY,
        on_publish_received=on_publish_received,
        client_id=CLIENT_ID
    )

    client.start()
    time.sleep(2)

    client.subscribe(subscribe_packet=mqtt5.SubscribePacket(
        subscriptions=[mqtt5.Subscription(topic_filter=TOPIC, qos=mqtt5.QoS.AT_LEAST_ONCE)]
    ))

    # Start the Firebase background listener
    print("Listening for Web App commands...")
    command_stream = db.child("commands").stream(command_handler)

    print("Listening for Raspberry Pi... Press Ctrl+C to stop.")
    print("Listening for Web App commands and checking schedule... Press Ctrl+C to stop.")

    # Define your local timezone (Romania)
    local_tz = pytz.timezone('Europe/Bucharest')
    last_fed_time = ""
try:
        while True:
            # 1. Get the current time in Romania (Format: "HH:MM")
            now = datetime.datetime.now(local_tz)
            current_time_str = now.strftime("%H:%M")

            # 2. We only need to check the schedule once per minute
            if current_time_str != last_fed_time:

                try:
                    # Fetch the latest schedule from Firebase
                    schedule_node = db.child("feeder_status").child("schedule").get().val()

                    if schedule_node:
                        # Convert the Firebase dictionary into a simple list of times
                        schedule_list = [v for k, v in schedule_node.items()]

                        # 3. If the current time matches a scheduled time!
                        if current_time_str in schedule_list:
                            print(f"\n[ALARM] It is {current_time_str}! Executing scheduled feeding...>

                            # Send the command to AWS IoT
                            payload = json.dumps({"feed_command": True})
                            client.publish(mqtt5.PublishPacket(
                                topic=COMMAND_TOPIC,
                                payload=payload,
                                qos=mqtt5.QoS.AT_LEAST_ONCE
                            ))

                            # Mark this minute as "fed" so it doesn't dispense 60 times in one minute!
                            last_fed_time = current_time_str

                except Exception as e:
                    print(f"Brief network timeout ignored: {e}")
            # Sleep for 5 seconds before checking the clock again
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nShutting down bridge...")
        command_stream.close()
        client.stop()

