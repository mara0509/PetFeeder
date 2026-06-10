import serial
import time

# Update this to match your port (/dev/ttyUSB0 or /dev/ttyACM0)
esp32_port = '/dev/ttyUSB0'
baud_rate = 115200

try:
    # Open the serial connection
    esp32 = serial.Serial(esp32_port, baud_rate, timeout=1)
    # The ESP32 restarts when a serial connection is opened. Wait for it to boot.
    time.sleep(2) 
    
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit()

def command_dispense():
    print("Sending DISPENSE command to ESP32...")
    # Send the command as bytes with a newline character
    esp32.write(b"DISPENSE\n")
    
    # Wait for the ESP32 to finish and reply "DONE"
    while True:
        if esp32.in_waiting > 0:
            response = esp32.readline().decode('utf-8').strip()
            if response == "DONE":
                print("ESP32 confirmed: Food dispensed!")
                break

if __name__ == '__main__':
    command_dispense()
