import RPi.GPIO as GPIO
import time
from hx711 import HX711

PIR_PIN = 7  
HX711_DT = 5
HX711_SCK = 6


CALIBRATION_FACTOR = 1228.859
ZERO_POINT = 304695.0


MAX_BOWL_CAPACITY_GRAMS = 500.0 


GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)
hx = HX711(HX711_DT, HX711_SCK)

def get_weight_in_grams():
    readings = []
    # Take 5 quick readings for average
    for _ in range(5):
        val_list = hx.get_raw_data()
        if val_list and len(val_list) > 0:
            raw_number = val_list[0]
            flipped_number = raw_number * -1  # Upside-down load cell fix
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
        # 1. Read PIR
        if GPIO.input(PIR_PIN):
            pet_detected = True

        # 2. Read Load Cell
        food_percentage=round(get_weight_in_grams(),1)
        if food_percentage<-0.5:
           food_percentage=0.0

    except Exception as e:
        print(f"Sensor error: {e}")

    return food_percentage, pet_detected
