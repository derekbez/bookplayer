# Copilot Instructions for BookPlayer Project

## Project Overview
This project is a Raspberry Pi-based audiobook player that uses RFID cards to select and play books. It interacts with GPIO buttons, status lights, and an MPD (Music Player Daemon) backend. The main entry point is `main.py` in the `bookplayer/` directory.

## System Requirements and Installation
- **Hardware Requirements**:
  - Raspberry Pi (tested on RPi 4)
  - RFID reader (compatible with nfcpy)
  - GPIO buttons and LEDs as per configuration
  - USB audio device or audio HAT for MPD output

- **System Setup**:
  - Python 3.11 or later
  - Virtual environment recommended:
    ```bash
    python3 -m venv ~/repo
    source ~/repo/bin/activate
    ```
  - GPIO and hardware dependencies:
    ```bash
    sudo apt install -y python3-rpi-lgpio
    sudo apt install -y libusb-1.0-0-dev libnfc-bin libnfc-dev libpcsclite-dev
    ```
  - GPIO configuration in `/boot/firmware/config.txt`:
    ```
    dtoverlay=gpio-shutdown,gpio_pin=3
    gpio=14=op,pd,dh
    ```
  - Books directory mount point:
    - Create directory: `sudo mkdir -p ~/books`
    - Add to `/etc/fstab`: `LABEL=BOOKS /home/rpi/books auto defaults,nofail 0 0`

- **Automatic Startup**:
  - `online_light.py` is started via crontab
  - MPD service should be enabled: `sudo systemctl enable mpd`
  - Configure MPD in `/etc/mpd.conf`

## Dependencies
- **System Services**:
  - **MPD (Music Player Daemon)**:
    - Required for audio playback
    - Install: `sudo apt-get install mpd`
    - Configuration in `/etc/mpd.conf`
    - Service management: `sudo systemctl start/stop/restart mpd`
    - Default port: 6600
    - Verify: `mpc status`

- **Python Packages**:
  - **nfcpy**:
    - Core RFID reading functionality
    - Install: `pip install nfcpy`
    - Requires USB permissions: `sudo usermod -a -G plugdev $USER`
    - Hardware support: USB NFC readers (e.g., SCL3711, ACR122U)
  - **python-mpd2**:
    - MPD client library
    - Install: `pip install python-mpd2`
    - Used by `player.py` for MPD communication
  - **RPi.GPIO**:
    - GPIO interface for Raspberry Pi
    - Usually pre-installed on Raspberry Pi OS
    - Used by `gpio_manager.py`

- **Development Dependencies**:
  - **pytest**: Testing framework
  - **pytest-mock**: Mocking support for pytest
  - Install: `pip install pytest pytest-mock`

## Key Components
- **main.py**: Application entry point, manages threads, signal handling, and the main event loop.
- **player.py**: Handles playback logic and MPD communication.
- **rfid.py**: Reads RFID cards to select books.
- **booklist.py**: Maps RFID card IDs to book IDs and titles.
- **gpio_manager.py**: Manages GPIO pin setup and edge detection.
- **status_light.py**: Controls the play status LED.
- **online_light.py**: Manages the online status indicator LED.
- **progress_manager.py**: Tracks and saves playback progress.
- **config.py**: Stores configuration such as GPIO pins, file paths, and MPD connection info.

## Coding Guidelines
- **Threading**: Use daemon threads for background tasks (e.g., button monitoring, status light).
- **Logging**: Use the `setup_logging()` function in `main.py` to configure logging. Log to both console and `bookplayer.log`.
- **Signal Handling**: Use `signal_handler` in `BookReader` to ensure clean shutdown and resource cleanup.
- **GPIO**: Use `GPIOManager` for all GPIO pin setup and edge detection. Avoid direct GPIO calls outside this class.
- **RFID**: Use the `rfid.Reader` class for card reading. Do not access RFID hardware directly elsewhere.
- **Player Actions**: All playback actions should go through the `Player` class. Button callbacks are mapped in `config.gpio_pins`.
- **Progress Tracking**: Use `ProgressManager` to save and restore playback position for each book.
- **Book Selection**: Use `BookList` to map RFID card IDs to book IDs and titles.

## Git Workflow
- **Branch Management**: 
  - The main branch should always be in a deployable state
  - Create feature branches for new development
  - Use meaningful branch names (e.g., `feature/dual-lights`, `fix/rfid-timeout`)
- **Pull Requests**:
  - Keep changes focused and atomic
  - Include test results or verification steps
  - Update documentation as needed
- **Merge Strategy**:
  - Use rebase to keep history clean: `git pull --rebase origin main`
  - Squash commits when merging feature branches
- **Version Control**:
  - Ignore generated files (*.pyc, *.log, *.db)
  - Keep sensitive configuration out of version control
  - Tag releases with semantic versioning

## Best Practices
- **Exception Handling**: Catch and log exceptions in threads and the main loop. Ensure all resources are cleaned up on error or shutdown.
- **Configuration**: Store all hardware pin numbers, file paths, and connection info in `config.py`.
- **Testing**: Place all test scripts in the `bookplayer/test/` directory. Use mock objects for hardware interfaces when possible.
- **Extensibility**: Add new hardware features by creating new manager classes (e.g., for additional sensors or outputs).
- **Dependency Injection**: Pass dependencies (e.g., `Player`, `ProgressManager`) into constructors instead of creating them inside classes. This improves testability and reduces coupling.
- **Event Bus**: Consider using an event bus for communication between components (e.g., GPIO, RFID, Player). This decouples components, allowing them to react to events without direct knowledge of each other, making the system more modular.


## Testing Framework
- **Test Structure**:
  ```
  bookplayer/test/
  ├── __init__.py
  ├── run_tests.py           # Test runner script
  ├── test_booklist.py      # BookList tests
  ├── test_gpio_manager.py  # GPIO tests
  ├── test_player.py        # Player tests
  ├── test_progress_manager.py
  ├── test_rfid.py          # RFID tests
  ├── test_status_led.py    # LED status tests
  └── test_status_light.py  # Status light tests
  ```

- **Test Setup**:
  ```python
  # Example test file structure
  import unittest
  from unittest.mock import Mock, patch
  
  class TestComponent(unittest.TestCase):
      def setUp(self):
          """Run before each test"""
          self.mock_dependencies()
          
      def tearDown(self):
          """Run after each test"""
          self.cleanup_resources()
          
      @retry_on_hardware_error()  # Decorator for hardware-related tests
      def test_feature(self):
          """Test specific feature"""
          pass
  ```

- **Mock Objects**:
  - Use `unittest.mock` for hardware dependencies
  - Mock GPIO pins, RFID reader, MPD client
  - Example:
    ```python
    @patch('rfid.nfc.ContactlessFrontend')
    def test_rfid_read(self, mock_nfc):
        mock_nfc.return_value.sense.return_value = mock_tag
        # Test RFID reading
    ```

- **Running Tests**:
  ```bash
  # Run all tests
  python3 -m pytest test/
  
  # Run specific test file
  python3 -m pytest test/test_rfid.py
  
  # Run with coverage
  python3 -m pytest --cov=bookplayer test/
  
  # Debug output
  python3 -m pytest -v --log-cli-level=DEBUG
  ```

- **Test Guidelines**:
  - Mock all hardware interactions:
    - GPIO pins via `@patch('RPi.GPIO')`
    - RFID reader via `@patch('rfid.nfc.ContactlessFrontend')`
    - MPD client via `@patch('mpd.MPDClient')`
  - Use decorators for retry logic on flaky tests
  - Keep tests focused and atomic
  - Validate resource cleanup in tearDown methods
  - Include both success and error cases
  - Test edge cases and timeouts
  - Mock file operations when testing booklist and progress management
  - Use pytest fixtures for common mock objects
  - Implement integration tests separately from unit tests
  - Test LED status patterns thoroughly
  - Verify proper thread cleanup in long-running operations

## Configuration Options
The following configuration options are available in `config.py`:

- **Database**:
  - `db_file`: Path to SQLite database for playback progress (default: `state.db` in project directory)

- **RFID Reader**:
  - Serial port settings in `serial` dict:
    - `port_name`: Serial port for RFID reader (default: "/dev/ttyAMA0")
    - `baudrate`: Serial baudrate (default: 9600)
    - `string_length`: Expected RFID string length (default: 14)

- **MPD Connection**:
  - Settings in `mpd_conn` dict:
    - `host`: MPD server host (default: "localhost")
    - `port`: MPD server port (default: 6600)

- **GPIO Configuration**:
  - Button configurations in `gpio_pins` list:
    - Pin 9: Rewind (2000ms debounce)
    - Pin 11: Toggle Pause (2000ms debounce)
    - Pin 22: Volume Down (1000ms debounce)
    - Pin 10: Volume Up (1000ms debounce)
  - Status LED pins:
    - `play_light_pin`: Play status LED (Pin 23)
    - `rewind_light_pin`: Rewind status LED (Pin 24)

- **File Paths**:
  - `booklist_filepath`: Path to book mapping CSV file (default: "/home/rpi/books/booklist.csv")
  - `cardslist_filepath`: Path to cards list CSV file (default: "./cardslist.csv")

## Running the Application
- Run the app from the `bookplayer/` directory:
  ```bash
  python3 main.py
  ```
- Ensure all hardware (RFID reader, buttons, lights) is connected as per the pin configuration in `config.py`.

## Troubleshooting
- **Common Issues**:
  - RFID reader not detected:
    - Verify USB permissions: `sudo usermod -a -G plugdev $USER`
    - Check serial port configuration in `config.py`
    - Test with `nfc-list` command
  
  - MPD playback issues:
    - Verify MPD service is running: `systemctl status mpd`
    - Check MPD configuration: `/etc/mpd.conf`
    - Test with `mpc status`
    - Verify audio device configuration
  
  - GPIO button problems:
    - Check physical connections
    - Verify pin numbers in `config.py`
    - Test GPIO pins: `gpio readall`
    - Check for conflicting pin usage
  
  - LED status lights not working:
    - Verify GPIO permissions
    - Check LED polarity
    - Test pins with `gpio write <pin> <1/0>`
  
  - Book progress not saving:
    - Check database file permissions
    - Verify database path in `config.py`
    - Check available disk space

- **Debug Mode**:
  - Enable debug logging in `main.py`
  - Use `pytest -v --log-cli-level=DEBUG` for verbose test output
  - Check `bookplayer.log` for detailed logs
  - Use `mpc` commands to test MPD directly

---

*This file is intended to help GitHub Copilot and other developers understand the structure and conventions of the BookPlayer project. Update as the project evolves.*
