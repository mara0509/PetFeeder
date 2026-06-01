import RPi.GPIO as GPIO
import time
from hx711 import HX711

#pin configuration
#which gpio pins are connected to the sensors
PIR_PIN = 7 #physical pin 26
HX711_DT = 5 # connected to data pin of amplifier
HX711_SCK = 6# connected to clock pin of the amplifier

#calibration value for the load cell
CALIBRATION_FACTOR = 1228.859#Converts raw sensor units into gram, this is what should be deducted to get the apropiate value in grams
ZERO_POINT = 304695.0 #value returned when the bowl is empty, that basically should be 0

#maximum capacity we set for the bowl, so we don't put too much weight, the bowl also tooked into consideration
MAX_BOWL_CAPACITY_GRAMS = 500.0 

#we use BCM numbering, we use the actual value of the GPIO, not the numbering on the schema like pin number 26
GPIO.setmode(GPIO.BCM)
#GPIO 7 is configured as an input pin
GPIO.setup(PIR_PIN, GPIO.IN)
#we have an amplifier HX711 object
hx = HX711(HX711_DT, HX711_SCK)

def get_weight_in_grams():
    readings = []
    #we take 5 quick readings
    for _ in range(5):
        val_list = hx.get_raw_data()
        if val_list and len(val_list) > 0:
            raw_number = val_list[0]
            flipped_number = raw_number * -1# a -1 here because we montat the load cell upside down by accident
            readings.append(flipped_number)
        time.sleep(0.05)

    if len(readings) > 0:
        average_raw = sum(readings) / len(readings)
        raw_without_bowl = average_raw - ZERO_POINT
        grams = raw_without_bowl / CALIBRATION_FACTOR
        return grams
    else:
        return 0.0

def get_sensor_data():
    """Reads both sensors and returns (food_percentage, pet_detected)"""
    pet_detected = False
    food_percentage = 0.0
    try:
        # we read the pir sensor
        if GPIO.input(PIR_PIN):
            pet_detected = True
        #get the load cell grams
        current_grams = get_weight_in_grams()
        percentage = (current_grams / MAX_BOWL_CAPACITY_GRAMS) * 100
        #value should stay between 0 and 100 to make sense
        food_percentage = max(0, min(100, round(percentage, 1)))
        #the percentage food is converted dynamically into grams in the react frontend
        #Math.round(live.food_percentage)

    except Exception as e:
        print(f"Sensor error: {e}")

    return food_percentage, pet_detected# what we get in return is (n grams, true/false)
