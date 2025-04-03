import RPi.GPIO as GPIO
import time

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Define GPIO pins for buttons and LEDs
button_group1 = [9, 11]
button_group2 = [10, 22]
led1 = 20
led2 = 21

# Set up buttons as input with pull-up resistors
for button in button_group1:
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for button in button_group2:
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set up LEDs as output
GPIO.setup(led1, GPIO.OUT)
GPIO.setup(led2, GPIO.OUT)

try:
    while True:
        # Check button states in group 1
        group1_active = any(GPIO.input(button) == GPIO.LOW for button in button_group1)
        # Check button states in group 2
        group2_active = any(GPIO.input(button) == GPIO.LOW for button in button_group2)
        
        # Control LEDs based on button states
        GPIO.output(led1, GPIO.HIGH if group1_active else GPIO.LOW)
        GPIO.output(led2, GPIO.HIGH if group2_active else GPIO.LOW)
        
        time.sleep(0.1)  # Delay to debounce button inputs

except KeyboardInterrupt:
    pass

finally:
    GPIO.cleanup()  # Clean up GPIO settings on exit
