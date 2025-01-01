import time
import RPi.GPIO as GPIO
import config

class GPIOTest:
    def __init__(self):
        self.setup_gpio()

    def setup_gpio(self):
        print("Setting up GPIO")
        """Setup all GPIO pins"""

        GPIO.setmode(GPIO.BCM)

        # Input pins for buttons
        for pin in config.gpio_pins:
            try:
                print(f"pin: {pin['pin_id']}")
                GPIO.setup(pin['pin_id'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(pin['pin_id'], GPIO.BOTH, callback=self.create_callback(pin['pin_id']), bouncetime=pin['bounce_time'])
            except RuntimeError as e:
                print(f"Error: {e} Pin: {pin}")

        # Output pins for LED
        GPIO.setup(20, GPIO.OUT)
        GPIO.setup(21, GPIO.OUT)

    def create_callback(self, pin_id):
        def callback(channel):
            button_state = GPIO.input(pin_id)
            if button_state == GPIO.LOW:
                GPIO.output(20, GPIO.HIGH)  # Turn on LED
            else:
                GPIO.output(20, GPIO.LOW)   # Turn off LED
            print(f"Button {pin_id} state: {'Pressed' if button_state == GPIO.LOW else 'Released'}")
        return callback

if __name__ == "__main__":
    g = GPIOTest()
    try:
        while True:
            time.sleep(1)  # Keep the program running to listen for events
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
