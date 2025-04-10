import RPi.GPIO as GPIO
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Define GPIO pins for buttons and LEDs
button_group1 = [9, 11]
button_group2 = [10, 22]
led1 = 20
led2 = 21

# Track previous button states
prev_group1_active = False
prev_group2_active = False

# Set up buttons as input with pull-up resistors
for button in button_group1:
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for button in button_group2:
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set up LEDs as output
GPIO.setup(led1, GPIO.OUT)
GPIO.setup(led2, GPIO.OUT)

logger.info("GPIO test started. Press Ctrl+C to exit")
logger.info(f"Group 1 buttons: {button_group1}")
logger.info(f"Group 2 buttons: {button_group2}")

try:
    while True:
        # Check button states in group 1
        group1_active = any(GPIO.input(button) == GPIO.LOW for button in button_group1)
        # Check button states in group 2
        group2_active = any(GPIO.input(button) == GPIO.LOW for button in button_group2)
        
        # Log button press events (only when state changes from inactive to active)
        if group1_active and not prev_group1_active:
            # Find which button in group 1 was pressed
            pressed = [b for b in button_group1 if GPIO.input(b) == GPIO.LOW]
            logger.info(f"Group 1 button(s) pressed: {pressed}")
            
        if group2_active and not prev_group2_active:
            # Find which button in group 2 was pressed
            pressed = [b for b in button_group2 if GPIO.input(b) == GPIO.LOW]
            logger.info(f"Group 2 button(s) pressed: {pressed}")
        
        # Update previous states
        prev_group1_active = group1_active
        prev_group2_active = group2_active
        
        # Control LEDs based on button states
        GPIO.output(led1, GPIO.HIGH if group1_active else GPIO.LOW)
        GPIO.output(led2, GPIO.HIGH if group2_active else GPIO.LOW)
        
        time.sleep(0.1)  # Delay to debounce button inputs

except KeyboardInterrupt:
    logger.info("GPIO test stopped by user")

finally:
    GPIO.cleanup()  # Clean up GPIO settings on exit
