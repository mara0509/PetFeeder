import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

# PIR connected to physical pin 26
pir = 26

GPIO.setup(pir, GPIO.IN)

print("Waiting for sensor to settle")
time.sleep(2)

print("Detecting motion")

try:
    while True:

        if GPIO.input(pir):
            print("Motion Detected!")
            time.sleep(2)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")
    GPIO.cleanup()
