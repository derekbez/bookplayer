# Refactoring the BookPlayer to an Event-Driven Architecture

This document outlines a plan to refactor the BookPlayer application from its current polling-based model to a more efficient and maintainable event-driven architecture.

## 1. Analysis of the Current Architecture

The current application works but relies heavily on polling within multiple loops, which has several drawbacks:

*   **High CPU Usage**: The `button_loop` and the main `loop` in `main.py` constantly check for state changes (button presses, RFID card scans, player status) in tight `while` loops with a small `sleep`. This consumes CPU cycles even when no user interaction is occurring.
*   **Tight Coupling**: The main `BookReader` class is a large orchestrator that is tightly coupled to all other components (`Player`, `RFIDReader`, `GPIOManager`, `StatusLED`). The main loop directly calls methods on these components, making it complex and difficult to modify or test in isolation.
*   **Delayed Response**: The response to an event is dependent on the polling interval. For example, a button press might not be detected for up to 50ms. While small, this is less efficient than an interrupt-driven approach.
*   **Difficult to Extend**: Adding a new source of interaction (e.g., a web interface, a new type of sensor) would require modifying the core loops, increasing their complexity and the risk of introducing bugs.

## 2. Proposed Event-Driven Architecture

An event-driven architecture decouples event sources (producers) from event handlers (consumers) using a central event queue.

1.  **Event Queue**: A single, thread-safe queue (like Python's `queue.Queue`) will act as the central message bus for the entire application.
2.  **Event Producers**: These components run in their own threads and are responsible for detecting external events and placing corresponding event objects onto the queue.
    *   **Button Manager**: Will use `RPi.GPIO`'s interrupt capabilities (`add_event_detect`) to instantly detect button presses and put a `ButtonPressed` event on the queue. This eliminates the need for the polling `button_loop`.
    *   **RFID Reader**: Will run in a dedicated thread, polling for cards. When a card is detected, it places a `CardScanned` event on the queue.
    *   **Player Monitor**: A new, simple thread could monitor the MPD player's status and emit `PlayerStateChanged` or `BookFinished` events. This decouples status-checking from other logic.
3.  **Event Consumer (Main Loop)**: The main loop will be greatly simplified. It will do only one thing: pull an event from the queue and pass it to a dispatcher. It will block when the queue is empty, consuming no CPU.
4.  **Event Handlers**: These are simple, focused functions that contain the business logic for handling a specific type of event. For example, `handle_button_press(event)` or `handle_card_scan(event)`.

### Conceptual Diagram

```
                                  +-----------------+
                                  |                 |
  (GPIO Interrupt) --[Button]---->|   Event Queue   |---->[Main Loop]--+
                                  |                 |                  |
  (Polling Thread) --[RFID]------>| (FIFO)          |                  |
                                  |                 |                  |
  (Polling Thread) --[Player]---->|                 |                  |
                                  +-----------------+                  |
                                                                       |
                                     +----------------------------------+
                                     |
                                     v
                              +----------------+
                              | Event Dispatcher |
                              +----------------+
                                     |
           +-------------------------+-------------------------+
           |                         |                         |
           v                         v                         v
  +------------------+    +-------------------+    +---------------------+
  | HandleButtonPress|    | HandleCardScanned |    | HandlePlayerState...|
  +------------------+    +-------------------+    +---------------------+

```

### Example Event Definitions

We can define simple data classes to represent our events.

```python
from dataclasses import dataclass

@dataclass
class ButtonPressed:
    pin_id: int
    callback_name: str

@dataclass
class CardScanned:
    card_id: int

@dataclass
class PlayerStateChanged:
    new_state: str  # e.g., 'play', 'pause', 'stop'
    status: dict    # Full status dictionary from MPD

@dataclass
class BookFinished:
    book_id: int

@dataclass
class UpdateProgress:
    """Event to trigger saving progress."""
    status: dict
```

### Refactored `main.py` (Conceptual)

The `BookReader` class would be restructured to manage the event producers and the consumer loop.

```python
import queue
from threading import Thread
import RPi.GPIO as GPIO

from bookplayer.led_manager import LEDManager # New import

# ... other imports

class BookReader:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.running = True

        # ... initialize player, progress_manager, gpio_manager etc. ...
        # The LEDManager now handles all LED setup and event handling
        self.led_manager = LEDManager(self.gpio_manager)

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Start event producers in threads
        Thread(target=self.rfid_producer, daemon=True).start()
        Thread(target=self.player_status_producer, daemon=True).start()
        self.setup_button_producers()

    def rfid_producer(self):
        """Polls RFID and puts CardScanned events on the queue."""
        # ... rfid reader setup ...
        while self.running:
            card = self.rfid_reader.read()
            if card:
                self.event_queue.put(CardScanned(card_id=card.get_id()))
            time.sleep(0.5) # Polling delay for RFID

    def setup_button_producers(self):
        """Sets up GPIO interrupts to produce ButtonPressed events."""
        for pin_config in config.gpio_pins:
            pin_id = pin_config['pin_id']
            self.gpio_manager.setup_pin(pin_id, "input", GPIO.PUD_UP)
            GPIO.add_event_detect(
                pin_id,
                GPIO.FALLING,
                callback=lambda p=pin_id, c=pin_config['callback']: self.event_queue.put(
                    ButtonPressed(pin_id=p, callback_name=c)
                ),
                bouncetime=pin_config['bounce_time']
            )

    def player_status_producer(self):
        """Polls player status and generates events."""
        # This is still polling, but it's isolated and its only job
        # is to translate state changes into events.
        last_state = None
        while self.running:
            status = self.player.get_status()
            current_state = status.get('state')
            if current_state and current_state != last_state:
                self.event_queue.put(PlayerStateChanged(new_state=current_state, status=status))
                last_state = current_state
            
            if self.player.is_playing():
                 self.event_queue.put(UpdateProgress(status=status))

            time.sleep(1) # Check status every second

    def main_loop(self):
        """The main event consumer loop."""
        while self.running:
            try:
                event = self.event_queue.get(timeout=1) # Block until an event
                self.dispatch_event(event)
            except queue.Empty:
                continue # No event, just loop

    def dispatch_event(self, event):
        """Calls the appropriate handler for an event."""
        # The LEDManager gets a chance to handle every event
        self.led_manager.handle_event(event)

        if isinstance(event, ButtonPressed):
            self.handle_button_press(event)
        elif isinstance(event, CardScanned):
            self.handle_card_scan(event)
        elif isinstance(event, UpdateProgress):
            self.handle_progress_update(event)
        # ... other event types

    # --- Event Handlers ---

    def handle_button_press(self, event: ButtonPressed):
        # This handler is now only for player actions, not LED feedback
        logger.info(f"Handling button press: {event.callback_name}")
        method = getattr(self.player, event.callback_name)
        method(event.pin_id)

    def handle_card_scan(self, event: CardScanned):
        # ... logic to look up book and start playing ...

    def handle_progress_update(self, event: UpdateProgress):
        # ... logic to save progress to DB from event.status ...

    def signal_handler(self, signal, frame):
        logger.info("Shutting down...")
        self.running = False
        self.led_manager.stop() # Add cleanup for LEDManager
        # ... other cleanup (player, gpio, etc.) ...

if __name__ == '__main__':
    reader = BookReader()
    reader.main_loop()
```

## 3. User Stories for Migration

This migration can be broken down into the following user stories, which can be implemented sequentially.

---

**Epic: Refactor to Event-Driven Architecture**

*   **Story 1: Establish Event Infrastructure**
    *   **As a** developer, **I want to** create a central, thread-safe event queue and define data classes for all application events (`ButtonPressed`, `CardScanned`, `PlayerStateChanged`, etc.), **so that** different parts of the application can communicate in a decoupled, standardized way.

*   **Story 2: Convert Button Polling to Event-Driven**
    *   **As a** developer, **I want to** replace the polling-based `button_loop` with interrupt-driven `GPIO.add_event_detect` callbacks, **so that** button presses are handled instantly, CPU usage is reduced, and a `ButtonPressed` event is placed on the queue.

*   **Story 3: Isolate RFID Reader Logic**
    *   **As a** developer, **I want to** move the RFID reader polling logic into its own dedicated producer thread, **so that** it can run independently and place a `CardScanned` event on the queue when a new card is detected, decoupling it from the main application loop.

*   **Story 4: Create an Event-Dispatching Main Loop**
    *   **As a** developer, **I want to** refactor the main application loop to be a simple consumer that blocks and waits for events from the queue and then dispatches them to specific handler functions, **so that** the core logic is simplified and only executes when necessary.

*   **Story 5: Refactor Player Actions into Event Handlers**
    *   **As a** developer, **I want to** create dedicated event handler functions for `ButtonPressed` and `CardScanned` events, **so that** the business logic for playing a book or performing a player action is cleanly separated from the event dispatching mechanism.

*   **Story 6: Decouple Status Light Updates**
    *   **As a** developer, **I want to** create a `PlayerStateChanged` event and a corresponding handler, **so that** the `StatusLED` patterns are updated reactively based on the player's state, rather than being determined by polling in the main loop.

*   **Story 7: Decouple Progress Saving**
    *   **As a** developer, **I want to** create an `UpdateProgress` event, produced periodically while a book is playing, **so that** the logic for saving playback progress is handled in its own decoupled handler and is no longer intertwined with the main loop's responsibilities.

---

## 4. Conclusion

By migrating to an event-driven architecture, the BookPlayer application will become more robust, performant, and developer-friendly. The clear separation of concerns will make it significantly easier to debug issues, test individual components, and add new features in the future without disturbing the existing, stable core.

## 5. Further Best Practice Improvements

Beyond the initial event-driven refactoring, the following user stories outline further steps to improve code quality, testability, and maintainability.

---

**Epic: Improve Code Quality and Maintainability**

*   **Story 8: Implement Dependency Injection**
    *   **As a** developer, **I want to** refactor the main application class (`BookReader`) to receive its dependencies (like `Player`, `ProgressManager`, `LEDManager`) via its constructor, **so that** components are decoupled (Inversion of Control) and can be easily replaced with mocks for unit testing.

*   **Story 9: Enhance Configuration Management**
    *   **As a** developer, **I want to** move configuration settings from `config.py` to a `.env` file or a YAML file, **so that** I can change deployment-specific settings (like file paths, connection details) without modifying the Python source code, making the application more portable.

*   **Story 10: Fully Decouple Player from UI Concerns**
    *   **As a** developer, **I want to** remove all `StatusLED` dependencies and logic from the `Player` class, **so that** the `Player` is solely responsible for controlling MPD and is completely unaware of UI elements like lights, adhering to the Single Responsibility Principle.

*   **Story 11: Establish a Unit Testing Framework**
    *   **As a** developer, **I want to** set up a `pytest` testing framework and write unit tests for core components like `ProgressManager`, `BookList`, and event handlers, **so that** I can verify functionality automatically and prevent regressions when making future changes.

*   **Story 12: Encapsulate Event Producers**
    *   **As a** developer, **I want to** encapsulate the logic for each event producer (e.g., RFID polling, Player status monitoring) into its own dedicated class that runs in a thread, **so that** the main application class is simplified and only responsible for orchestrating the components, not implementing their internal logic.

*   **Story 13: Consolidate and Modernize Documentation**
    *   **As a** new user, **I want to** have a single, up-to-date installation guide that uses the `systemd` service for application startup (instead of `crontab`), **so that** the setup process is clear, reliable, and follows modern Linux best practices.

*   **Story 14: Improve Application Resilience**
    *   **As a** developer, **I want to** implement more robust error handling in the main event loop and within event producers, **so that** the application can gracefully handle and log unexpected errors (e.g., a disconnected peripheral) without crashing.

---

By migrating to an event-driven architecture, the BookPlayer application will become more robust, performant, and developer-friendly. The clear separation of concerns will make it significantly easier to debug issues, test individual components, and add new features in the future without disturbing the existing, stable core.