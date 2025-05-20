# Copilot Instructions for BookPlayer Project

## Project Overview
This project is a Raspberry Pi-based audiobook player that uses RFID cards to select and play books. It interacts with GPIO buttons, status lights, and an MPD (Music Player Daemon) backend. The main entry point is `main.py` in the `bookplayer/` directory.

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
  - Mock all hardware interactions
  - Use decorators for retry logic on flaky tests
  - Keep tests focused and atomic
  - Validate resource cleanup
  - Include both success and error cases
  - Test edge cases and timeouts

## Running the Application
- Run the app from the `bookplayer/` directory:
  ```bash
  python3 main.py
  ```
- Ensure all hardware (RFID reader, buttons, lights) is connected as per the pin configuration in `config.py`.

---

*This file is intended to help GitHub Copilot and other developers understand the structure and conventions of the BookPlayer project. Update as the project evolves.*
