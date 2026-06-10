import RPi.GPIO as GPIO
import time
import sys
from hx711 import HX711

# Setup
GPIO.setmode(GPIO.BCM)
hx = HX711(5, 6)

# A custom function to safely read the sensor, handle the list bug, 
# and fix the upside-down load cell all at once.
def get_clean_reading():
    readings = []
    print("Reading sensor...")
    
    # Take 10 readings to get a really smooth, accurate average
    for _ in range(10):
        val_list = hx.get_raw_data()
        
        if val_list and len(val_list) > 0:
            raw_number = val_list[0]
            # Fix the upside-down load cell
            flipped_number = raw_number * -1
            readings.append(flipped_number)
            
        time.sleep(0.1)
        
    if len(readings) > 0:
        average = sum(readings) / len(readings)
        return average
    else:
        print("Error: Could not read sensor.")
        return 0

try:
    print("\n--- HX711 CALIBRATION ---")
    print("1. Make sure the bowl is completely EMPTY.")
    input("Press ENTER to zero (tare) the scale...")

    zero_point = get_clean_reading()
    print("Bowl weight ignored! Scale is zeroed.")

    print("\n2. Place your 100g packet into the bowl.")
    input("Press ENTER when it is resting completely inside...")

    weight_with_item = get_clean_reading()
    
    # Calculate the difference the 100g packet made
    raw_difference = weight_with_item - zero_point
    
    # Calculate the magic number
    known_weight = 100.0
    calibration_factor = raw_difference / known_weight
    
    print("\n===========================================")
    print(f"YOUR CALIBRATION FACTOR IS: {calibration_factor}")
    print(f"YOUR ZERO POINT IS: {zero_point}")
    print("===========================================\n")
    print("Write both of these numbers down!")

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    GPIO.cleanup()
    sys.exit()
