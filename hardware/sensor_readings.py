import RPi.GPIO as GPIO
import time
from hx711 import HX711

# ==========================================
# PIN CONFIGURATION (ALL IN BCM MODE)
# ==========================================
PIR_PIN = 7     # This is Physical Pin 26!
HX711_DT = 5
HX711_SCK = 6

# ==========================================
# YOUR CALIBRATION NUMBERS
# ==========================================
CALIBRATION_FACTOR = 1228.859
ZERO_POINT = 304695.0

# Set this to the weight (in grams) when the bowl is 100% full
MAX_BOWL_CAPACITY_GRAMS = 500.0 

# ==========================================
# HARDWARE SETUP
# ==========================================
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
        current_grams = get_weight_in_grams()

        # 3. Calculate Percentage
        percentage = (current_grams / MAX_BOWL_CAPACITY_GRAMS) * 100
        
        # Clamp between 0% and 100% and round to 1 decimal
        food_percentage = max(0, min(100, round(percentage, 1)))

    except Exception as e:
        print(f"Sensor error: {e}")

    return food_percentage, pet_detected
