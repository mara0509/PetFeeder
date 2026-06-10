import RPi.GPIO as GPIO
import time
import sys
from hx711 import HX711

# ==========================================
# YOUR MAGIC CALIBRATION NUMBERS
# ==========================================
CALIBRATION_FACTOR = 1228.859
ZERO_POINT = 304695.0

# Setup GPIO and HX711
GPIO.setmode(GPIO.BCM)
hx = HX711(5, 6)

def get_weight_in_grams():
    """Reads the sensor, fixes the upside-down load cell, and calculates grams."""
    readings = []
    
    # Take 5 quick readings to get a smooth, accurate average
    for _ in range(5):
        val_list = hx.get_raw_data()
        
        # Check if we got valid data to avoid the empty list bug
        if val_list and len(val_list) > 0:
            raw_number = val_list[0]
            flipped_number = raw_number * -1  # Upside-down load cell fix
            readings.append(flipped_number)
            
        time.sleep(0.1)
        
    if len(readings) > 0:
        # 1. Get the average raw value
        average_raw = sum(readings) / len(readings)
        
        # 2. Subtract the weight of the empty bowl (Zero Point)
        raw_without_bowl = average_raw - ZERO_POINT
        
        # 3. Divide by the calibration factor to get exact grams
        grams = raw_without_bowl / CALIBRATION_FACTOR
        return grams
    else:
        return 0.0

try:
    print("Starting Pet Feeder Scale...")
    print("Press Ctrl+C to stop.")
    print("----------------------------")
    
    while True:
        # Get the weight
        current_weight = get_weight_in_grams() * (-1)
        
        # Print it nicely formatted to 1 decimal place
        print(f"Food in bowl: {current_weight:.1f} g")
        
        # Wait half a second before reading again
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nShutting down pet feeder...")
finally:
    GPIO.cleanup()
    sys.exit()
