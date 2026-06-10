# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from awsiot import mqtt5_client_builder
from awscrt import mqtt5
import threading, time
import serial
import argparse, uuid
from sensor_readings import get_sensor_data
import json


try:
   
    esp32 = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    print("Connected to ESP32 via USB!")
except Exception as e:
    print(f" Could not connect to ESP32: {e}")
    esp32 = None


parser = argparse.ArgumentParser(
    description="MQTT5 X509 Sample (mTLS)",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
required = parser.add_argument_group("required arguments")
optional = parser.add_argument_group("optional arguments")

required.add_argument("--endpoint", required=True, metavar="", dest="input_endpoint", help="IoT endpoint hostname")
required.add_argument("--cert", required=True, metavar="", dest="input_cert", help="Path to the certificate file")
required.add_argument("--key", required=True, metavar="", dest="input_key", help="Path to the private key file")

optional.add_argument("--client_id", metavar="",dest="input_clientId", default=f"mqtt5-sample-{uuid.uuid4().hex[:8]}", help="Client ID")
optional.add_argument("--topic", metavar="",default="test/topic", dest="input_topic", help="Topic")
optional.add_argument("--message", metavar="",default="Hello from mqtt5 sample", dest="input_message", help="Message payload")
optional.add_argument("--count", type=int, metavar="",default=5, dest="input_count", help="Messages to publish (0 = infinite)")

args = parser.parse_args()


TIMEOUT = 100
message_count = args.input_count
message_topic = args.input_topic
message_string = args.input_message

connection_success_event = threading.Event()
stopped_event = threading.Event()
received_all_event = threading.Event()
received_count = 0


# CALLBACK: ON MESSAGE RECEIVED

def on_publish_received(publish_packet_data):
    publish_packet = publish_packet_data.publish_packet
    topic = publish_packet.topic
    payload = publish_packet.payload.decode('utf-8')

    # 1. Check if this is a command from the Web App
    if topic == "feeder/commands":
        try:
            command_data = json.loads(payload)
            if command_data.get("feed_command") == True:
                print("\n BINGO! DISPENSE COMMAND RECEIVED FROM THE CLOUD! ")
                
                # TRIGGER THE ESP32 TO SPIN THE SERVO
                if esp32:
                    esp32.write(b"DISPENSE\n")
                    print("ISPENSE'command to ESP32 via USB!")
                else:
                    print("esp32 not connected. Cannot dispense.")
        except Exception as e:
            print(f"Command error: {e}")
            
    # 2. Standard behavior for sensor data echo
    else:
        print(f"==== Received message from topic '{topic}': {payload} ====\n")
        global received_count
        received_count += 1
        if received_count == args.input_count:
            received_all_event.set()

def on_lifecycle_stopped(lifecycle_stopped_data: mqtt5.LifecycleStoppedData):
    print("Lifecycle Stopped\n")
    stopped_event.set()

def on_lifecycle_attempting_connect(lifecycle_attempting_connect_data: mqtt5.LifecycleAttemptingConnectData):
    print("Lifecycle Connection Attempt\nConnecting to endpoint: '{}' with client ID'{}'".format(
        args.input_endpoint, args.input_clientId))

def on_lifecycle_connection_success(lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData):
    connack_packet = lifecycle_connect_success_data.connack_packet
    print("Lifecycle Connection Success with reason code:{}\n".format(repr(connack_packet.reason_code)))
    connection_success_event.set()

def on_lifecycle_connection_failure(lifecycle_connection_failure: mqtt5.LifecycleConnectFailureData):
    print("Lifecycle Connection Failure with exception:{}".format(lifecycle_connection_failure.exception))

def on_lifecycle_disconnection(lifecycle_disconnect_data: mqtt5.LifecycleDisconnectData):
    print("Lifecycle Disconnected with reason code:{}".format(
        lifecycle_disconnect_data.disconnect_packet.reason_code if lifecycle_disconnect_data.disconnect_packet else "None"))


if __name__ == '__main__':
    print("\nStarting 2-Way Smart Feeder Hardware Node\n")

    client = mqtt5_client_builder.mtls_from_path(
        endpoint=args.input_endpoint,
        cert_filepath=args.input_cert,
        pri_key_filepath=args.input_key,
        on_publish_received=on_publish_received,
        on_lifecycle_stopped=on_lifecycle_stopped,
        on_lifecycle_attempting_connect=on_lifecycle_attempting_connect,
        on_lifecycle_connection_success=on_lifecycle_connection_success,
        on_lifecycle_connection_failure=on_lifecycle_connection_failure,
        on_lifecycle_disconnection=on_lifecycle_disconnection,
        client_id=args.input_clientId)

    print("==== Starting client ====")
    client.start()

    if not connection_success_event.wait(TIMEOUT):
        raise TimeoutError("Connection timeout")

    # Subscribe to BOTH topics
    print("==== Subscribing to topics ====")
    subscribe_future = client.subscribe(subscribe_packet=mqtt5.SubscribePacket(
        subscriptions=[
            mqtt5.Subscription(topic_filter=message_topic, qos=mqtt5.QoS.AT_LEAST_ONCE),
            mqtt5.Subscription(topic_filter="feeder/commands", qos=mqtt5.QoS.AT_LEAST_ONCE)
        ]
    ))
    suback = subscribe_future.result(TIMEOUT)
    print("Suback received with reason code:{}\n".format(suback.reason_codes))

    # Continuous Sensor Publish Loop
    print("==== Starting continuous sensor publish loop. Press Ctrl+C to stop ====\n")
    try:
        while True:
            # 1. Grab your real hardware data
            food_pct, pet_status = get_sensor_data()

            # 2. Format it cleanly as JSON
            payload_dict = {
                "food_percentage": food_pct,
                "pet_detected": pet_status
            }
            json_payload = json.dumps(payload_dict)

            # 3. Publish to AWS IoT Core
            print(f"Publishing to '{message_topic}': {json_payload}")
            publish_future = client.publish(mqtt5.PublishPacket(
                topic=message_topic,
                payload=json_payload,
                qos=mqtt5.QoS.AT_LEAST_ONCE
            ))
            publish_completion_data = publish_future.result(TIMEOUT)
            
            # Wait 2 seconds before checking sensors again
            time.sleep(2.0)

    except KeyboardInterrupt:
        print("\nInterrupt received! Exiting loop...")

    # Graceful Shutdown
    print("==== Unsubscribing from topics ====")
    unsubscribe_future = client.unsubscribe(unsubscribe_packet=mqtt5.UnsubscribePacket(
        topic_filters=[message_topic, "feeder/commands"]))
    unsuback = unsubscribe_future.result(TIMEOUT)

    print("==== Stopping Client ====")
    client.stop()

    if not stopped_event.wait(TIMEOUT):
        raise TimeoutError("Stop timeout")

    print("==== Client Stopped! ====")
