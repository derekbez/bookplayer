# BookPlayer: RFID-Activated Audiobook Player for Raspberry Pi

## Overview
BookPlayer is an interactive audiobook player designed for the Raspberry Pi. It allows users to play audiobooks by scanning RFID cards, with playback and navigation controlled via physical buttons. The system is ideal for children or visually impaired users, providing a simple, tangible interface for audiobook selection and playback.

## Features
- **RFID Card Selection:** Each audiobook is associated with an RFID card. Scanning a card starts playback of the corresponding book.
- **Physical Button Controls:** Four GPIO-connected buttons provide simple playback control:
  - **Pause/Play Toggle (GPIO 11):** Toggle between playing and pausing the current audiobook.
  - **Rewind (GPIO 9):** Rewind playback by 20 seconds. If pressed near the start of a track, jumps to the previous track or the start of the current one.
  - **Volume Up (GPIO 10):** Increase playback volume by 10%.
  - **Volume Down (GPIO 22):** Decrease playback volume by 10%.
- **Progress Tracking:** The player remembers the last position for each book and resumes from where the user left off.
- **Status Light:** An LED status light provides visual feedback for playback state (playing, paused, stopped, etc.).
- **Robust Logging:** Application events and errors are logged to both the console and a rotating log file.

## User Interactions
1. **Start the Application:**
   - Run `main.py` on your Raspberry Pi. The system initializes hardware, logging, and background threads.
2. **Scan an RFID Card:**
   - Place an RFID card on the reader. If the card is recognized, playback of the associated audiobook begins or resumes from the last saved position.
   - If a different card is scanned, playback of the current book stops and the new book starts.
3. **Use Physical Buttons:**
   - Use the four physical buttons for playback control:
     - **Pause/Play Toggle:** Press to pause or resume playback.
     - **Rewind:** Press to rewind 20 seconds (or to the previous track/start if near the beginning).
     - **Volume Up/Down:** Press to adjust the playback volume in 10% increments.
   - There are no Next/Previous track buttons; navigation is limited to the above controls.
4. **Status Light Feedback:**
   - The status LED indicates the current state: solid (stopped), blinking (playing), or alternate patterns for pause/rewind.
5. **Automatic Progress Saving:**
   - While playing, the system periodically saves your position. When a book is finished, progress is cleared.
6. **Shutdown:**
   - The application can be safely stopped via SIGINT/SIGTERM (Ctrl+C or system signal), ensuring all resources are cleaned up.

## Output
- **Audio Playback:** Audiobooks are played through the Raspberry Pi's audio output.
- **Visual Feedback:** The status LED reflects the current playback state.
- **Logs:** Application activity and errors are written to `bookplayer.log` and the console.

## Technologies Used
- **Python 3**
- **RPi.GPIO:** For interfacing with Raspberry Pi GPIO pins (buttons, status light).
- **MPD (Music Player Daemon):** For audio playback (via the `Player` class).
- **RFID Reader:** For detecting and reading RFID cards (via the `rfid` module).
- **Threading:** For concurrent button and status light monitoring.
- **Logging:** Standard Python logging with rotating file handler.
- **SQLite (via ProgressManager):** For saving and restoring playback progress.

## File Structure
- `main.py`: Application entry point and main event loop.
- `booklist.py`: Manages the list of available books and RFID associations.
- `player.py`: Controls audio playback and interacts with MPD.
- `rfid.py`: Handles RFID card reading.
- `status_light.py`: Controls the status LED.
- `gpio_manager.py`: Manages GPIO pin setup and button edge detection.
- `progress_manager.py`: Handles saving and loading playback progress.
- `config.py`: Configuration for pins, file paths, and other settings.

## Setup & Requirements
1. **Hardware:**
   - Raspberry Pi (any model with GPIO support)
   - RFID reader (compatible with the `rfid` module)
   - Four physical buttons wired to GPIO pins (9, 10, 11, 22)
   - Status LED
2. **Software:**
   - Python 3
   - RPi.GPIO
   - MPD and Python MPD client
   - Other dependencies as required by the modules
3. **Configuration:**
   - Edit `config.py` to set up GPIO pins, file paths, and MPD connection details.
   - Prepare your audiobooks and associate them with RFID cards in the book list file.

## Running the Application
```sh
python3 main.py
```

## License
MIT License (see LICENSE file)
