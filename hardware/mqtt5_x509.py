# these are librariesprovided by the AWS
# connection to aws iot core,publish mqtt messages, subscribe to mqtt topics, receive mqtt messages
from awsiot import mqtt5_client_builder
from awscrt import mqtt5
#threading is used to synchronize events such as connection success.
#time is used to create delays between sensor readings
import threading, time

#used for the communication between usb and esp32
import serial

#process command line arguments
import argparse, uuid
#we import the get_sensor_data function from the sensors file
# so we get the values that were read from the sensors
from sensor_readings import get_sensor_data

#used to convert dictionaries from python into JSON, since JSON is the format we want to send to the AWS ioT core
import json

#connection done between the raspberrypi and the esp32
try:
    #opens up the connection between the esp32 and raspberry through th usb usb-c
    esp32 = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    #/dev/ttyUSB0 - port where linux detected the esp32, 115200 - communication speed
    print("Connected to ESP32 via USB!")
except Exception as e:
    print(f" Could not connect to ESP32: {e}")
    esp32 = None

#mechanism for reading parameters from the terminal
parser = argparse.ArgumentParser(
    description="MQTT5 X509 Sample (mTLS)",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)


required = parser.add_argument_group("required arguments")
optional = parser.add_argument_group("optional arguments")

#aws iot core adress - that long aws adress we got
required.add_argument("--endpoint", required=True, metavar="", dest="input_endpoint", help="IoT endpoint hostname")
#path to the certificate
required.add_argument("--cert", required=True, metavar="", dest="input_cert", help="Path to the certificate file")
#path to the private key file
required.add_argument("--key", required=True, metavar="", dest="input_key", help="Path to the private key file")
#with these 3 we identify what hardware device the aws is communicating with


#other arguments we need from the command line, the topic we subscribe to, the message, how much to publish onto the topic
optional.add_argument("--client_id", metavar="",dest="input_clientId", default=f"mqtt5-sample-{uuid.uuid4().hex[:8]}", help="Client ID")
optional.add_argument("--topic", metavar="",default="test/topic", dest="input_topic", help="Topic")
optional.add_argument("--message", metavar="",default="Hello from mqtt5 sample", dest="input_message", help="Message payload")
optional.add_argument("--count", type=int, metavar="",default=5, dest="input_count", help="Messages to publish (0 = infinite)")

args = parser.parse_args()


TIMEOUT = 100
message_count = args.input_count
message_topic = args.input_topic
message_string = args.input_message

#these are synchronization flags

#used to indicate aws connection established
connection_success_event = threading.Event()
#Used when shutting down
stopped_event = threading.Event()
#Have we received all expected messages
received_all_event = threading.Event()
#Counts how many MQTT messages have been received
received_count = 0


#callback is a function that AWS MQTT automatically executes whenever
#a message arrives on a topic that the Raspberry Pi is subscribed to.
#aws always calls this function when it needs
def on_publish_received(publish_packet_data):
    #extract mqtt package
    publish_packet = publish_packet_data.publish_packet
    #extract topic- either Test1 or petfeeder/commands
    topic = publish_packet.topic
    payload = publish_packet.payload.decode('utf-8')
    #mqtt transmits bytes so something like this (b'{"feed_command":true}')- this would be represented in bytes aarives and needs to be converted into a normal string '{"feed_command":true}'

    #based on topic we can 2 two actions
    #first is dispense food
    if topic == "feeder/commands":
        try:
            #converts json into something python can work with
            command_data = json.loads(payload)
            if command_data.get("feed_command") == True:
                print("\nDISPENSE COMMAND RECEIVED FROM THE CLOUD! ")
                #this is for the raspberry pi terminal
                
                #trigger the servomotor to move
                if esp32:
                    #when the button press from the web becomes an actual command, physical command
                    esp32.write(b"DISPENSE\n")
                    print("ent 'DISPENSE' command to ESP32 via USB!")
                else:
                    print("ESP32 not connected. Cannot dispense.")
        except Exception as e:
            print(f"Command error: {e}")
    else:
        print(f"Received message from topic '{topic}': {payload}\n")
        global received_count
        received_count += 1
        if received_count == args.input_count:
            received_all_event.set()

#when we stop the connection
def on_lifecycle_stopped(lifecycle_stopped_data: mqtt5.LifecycleStoppedData):
    print("Lifecycle Stopped\n")
    stopped_event.set()

#Runs whenever the client tries to connect
def on_lifecycle_attempting_connect(lifecycle_attempting_connect_data: mqtt5.LifecycleAttemptingConnectData):
    print("Lifecycle Connection Attempt\nConnecting to endpoint: '{}' with client ID'{}'".format(
        args.input_endpoint, args.input_clientId))
#when AWS accepts the connection
def on_lifecycle_connection_success(lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData):
    connack_packet = lifecycle_connect_success_data.connack_packet
    print("Lifecycle Connection Success with reason code:{}\n".format(repr(connack_packet.reason_code)))
    connection_success_event.set()#this signals the connection was established

#connection failure
def on_lifecycle_connection_failure(lifecycle_connection_failure: mqtt5.LifecycleConnectFailureData):
    print("Lifecycle Connection Failure with exception:{}".format(lifecycle_connection_failure.exception))

#connection is lost
def on_lifecycle_disconnection(lifecycle_disconnect_data: mqtt5.LifecycleDisconnectData):
    print("Lifecycle Disconnected with reason code:{}".format(
        lifecycle_disconnect_data.disconnect_packet.reason_code if lifecycle_disconnect_data.disconnect_packet else "None"))


if __name__ == '__main__':
    print("\nStarting 2-Way Smart Feeder Hardware Node\n")

    #we create the secure mqtt client
    #The MQTT client is the software object that allows the Raspberry Pi to communicate with AWS IoT Core.
    #the communication channel between the two
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

    print("Starting client")
    client.start()# this starts the connection

    #The script pauses until AWS confirms the connection
    if not connection_success_event.wait(TIMEOUT):
        raise TimeoutError("Connection timeout")

    #both topics need to be subscribed to
    print("Subscribing to topics")
    #and subscribe tells me to send me all the messages on these 2 topics from bellow
    subscribe_future = client.subscribe(subscribe_packet=mqtt5.SubscribePacket(
        subscriptions=[
            mqtt5.Subscription(topic_filter=message_topic, qos=mqtt5.QoS.AT_LEAST_ONCE),
            mqtt5.Subscription(topic_filter="petfeeder/commands", qos=mqtt5.QoS.AT_LEAST_ONCE)
        ]
    ))
    suback = subscribe_future.result(TIMEOUT)
    print("Suback received with reason code:{}\n".format(suback.reason_codes))

    #Continuous Sensor Publish Loop
    print("Starting continuous sensor publish loop. Press Ctrl+C to stop\n")
    try:
        while True:
            food_pct, pet_status = get_sensor_data()
            payload_dict = {
                "food_percentage": food_pct,
                "pet_detected": pet_status
            }
            json_payload = json.dumps(payload_dict)

            #publish to aws iot core
            print(f"Publishing to '{message_topic}': {json_payload}")
            #publish means sending data to the AWS
            publish_future = client.publish(mqtt5.PublishPacket(
                topic=message_topic,
                payload=json_payload,
                qos=mqtt5.QoS.AT_LEAST_ONCE
            ))
            publish_completion_data = publish_future.result(TIMEOUT)
            
            #wait 2 sec before checking sensors again
            time.sleep(2.0)

    except KeyboardInterrupt:
        print("\nInterrupt received! Exiting loop...")

    #shutdown
    print("Unsubscribing from topics")
    unsubscribe_future = client.unsubscribe(unsubscribe_packet=mqtt5.UnsubscribePacket(
        topic_filters=[message_topic, "feeder/commands"]))
    unsuback = unsubscribe_future.result(TIMEOUT)

    print("Stopping Client")
    client.stop()

    if not stopped_event.wait(TIMEOUT):
        raise TimeoutError("Stop timeout")

    print(" Client Stopped!")
