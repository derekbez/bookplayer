#!/usr/bin/env python
# encoding: utf-8

import logging
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

class GPIOManager:
    """Centralized GPIO management for buttons and status light."""

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.pins = {}
        self.last_state = {}

    def setup_pin(self, pin_id: int, mode: str, pull_up_down=None):
        """Set up a GPIO pin as input or output."""
        if mode == "input":
            GPIO.setup(pin_id, GPIO.IN, pull_up_down=pull_up_down)
            self.last_state[pin_id] = GPIO.input(pin_id)
        elif mode == "output":
            GPIO.setup(pin_id, GPIO.OUT)
        self.pins[pin_id] = mode
        logger.info(f"GPIO pin {pin_id} set up as {mode}")

    def has_edge_occurred(self, pin_id: int) -> bool:
        """Check if pin state has changed since last check."""
        if self.pins.get(pin_id) == "input":
            current_state = GPIO.input(pin_id)
            if current_state != self.last_state.get(pin_id):
                self.last_state[pin_id] = current_state
                return current_state == GPIO.LOW  # Return True only on press (FALLING)
        return False

    def set_pin_high(self, pin_id: int):
        """Set a GPIO pin to HIGH."""
        if self.pins.get(pin_id) == "output":
            GPIO.output(pin_id, GPIO.HIGH)

    def set_pin_low(self, pin_id: int):
        """Set a GPIO pin to LOW."""
        if self.pins.get(pin_id) == "output":
            GPIO.output(pin_id, GPIO.LOW)

    def cleanup_pin(self, pin_id: int):
        """Clean up a specific GPIO pin."""
        if pin_id in self.pins:
            GPIO.cleanup(pin_id)
            del self.pins[pin_id]

    def cleanup(self):
        """Clean up all GPIO pins."""
        GPIO.cleanup()

if __name__ == '__main__':
    import time
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting GPIO test...")
    
    # Suppress GPIO warnings about channels in use
    GPIO.setwarnings(False)
    # Clean up any existing GPIO configurations
    GPIO.cleanup()
    
    # Initialize GPIO manager
    gpio_manager = GPIOManager()
    
    # Define control pins (matching main application config)
    rewind_pin = 9
    pause_pin = 11
    vol_down_pin = 22
    vol_up_pin = 10
    
    # Define LED pins for feedback
    status_led = 20   # Shows play/pause state
    volume_led = 21   # Shows volume changes
    
    # Set up control buttons as inputs with pull-up resistors
    control_pins = [rewind_pin, pause_pin, vol_down_pin, vol_up_pin]
    for pin in control_pins:
        gpio_manager.setup_pin(pin, mode="input", pull_up_down=GPIO.PUD_UP)
        
    # Set up LEDs as outputs
    gpio_manager.setup_pin(status_led, mode="output")
    gpio_manager.setup_pin(volume_led, mode="output")
    
    # Track player state
    is_playing = False
    volume_level = 5  # 0-10
    
    try:
        logger.info("GPIO test running. Press Ctrl+C to exit...")
        logger.info("Controls:")
        logger.info(f"  Pin {pause_pin}: Toggle play/pause")
        logger.info(f"  Pin {rewind_pin}: Rewind")
        logger.info(f"  Pin {vol_up_pin}: Volume up")
        logger.info(f"  Pin {vol_down_pin}: Volume down")
        
        while True:
            # Check play/pause button
            if gpio_manager.has_edge_occurred(pause_pin):
                is_playing = not is_playing
                logger.info(f"{'Playing' if is_playing else 'Paused'}")
                gpio_manager.set_pin_high(status_led) if is_playing else gpio_manager.set_pin_low(status_led)
            
            # Check volume controls
            if gpio_manager.has_edge_occurred(vol_up_pin) and volume_level < 10:
                volume_level += 1
                logger.info(f"Volume up: {volume_level}")
                gpio_manager.set_pin_high(volume_led)
                time.sleep(0.1)
                gpio_manager.set_pin_low(volume_led)
                
            if gpio_manager.has_edge_occurred(vol_down_pin) and volume_level > 0:
                volume_level -= 1
                logger.info(f"Volume down: {volume_level}")
                gpio_manager.set_pin_high(volume_led)
                time.sleep(0.1)
                gpio_manager.set_pin_low(volume_led)
            
            # Check rewind button
            if gpio_manager.has_edge_occurred(rewind_pin):
                logger.info("Rewind pressed")
                # Flash both LEDs to indicate rewind
                gpio_manager.set_pin_high(status_led)
                gpio_manager.set_pin_high(volume_led)
                time.sleep(0.2)
                gpio_manager.set_pin_low(status_led)
                gpio_manager.set_pin_low(volume_led)
            
            time.sleep(0.05)  # Small delay to prevent CPU hogging
            
    except KeyboardInterrupt:
        logger.info("GPIO test stopped by user")
    finally:
        gpio_manager.cleanup()  # Clean up GPIO settings on exit
