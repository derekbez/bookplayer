
### **System Preparation**
1. **Update and upgrade the system** to ensure all packages are up-to-date:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

### **Install Git and Configure User Details**
2. Install Git and set up your username and email:
   ```bash
   sudo apt install -y git
   git config --global user.name "derekbez"
   git config --global user.email "derek@be-easy.com"
   ```

### **Set Up Python Environment**
3. Create a Python virtual environment for your project:
   ```bash
   python -m venv repo
   cd repo
   source bin/activate
   echo "source ~/repo/bin/activate" >> ~/.bashrc
   ```

### **Install Python and Required Libraries**
4. Install Python, pip, and essential development packages:
   ```bash
   sudo apt install python3 python3-pip python3-dev build-essential
   python -m ensurepip
   python -m pip install --upgrade pip
   sudo apt install -y python3-rpi-lgpio python3-debugpy
   ```

5. Install necessary Python libraries for GPIO and debugging:
   ```bash
   pip install RPi.GPIO debugpy
   ```

### **Clone Your GitHub Repository**
6. Clone your application repository:
   ```bash
   git clone https://github.com/derekbez/bookplayer.git bookplayer
   ```

### **Install NFC Libraries**
7. Install NFC libraries for interacting with NFC devices:
   ```bash
   pip install nfcpy
   sudo apt install -y libusb-1.0-0-dev libnfc-bin libnfc-dev libpcsclite-dev
   ```

### **Set Up MPD (Music Player Daemon)**
8. Install MPD and its Python client library:
   ```bash
   sudo apt-get install -y mpd
   pip install python-mpd2
   ```

9. Enable and start the MPD service:
   ```bash
   sudo systemctl enable mpd
   sudo systemctl start mpd
   sudo systemctl status mpd
   ```

10. Optionally, install MPC for debugging MPD:
    ```bash
    sudo apt-get install -y mpc
    ```

### **Clean Up and Configure File System**
11. Remove unnecessary packages:
    ```bash
    sudo apt autoremove
    ```

12. Set up directories and persistent mounts for storing books:
    - Create the directory: `sudo mkdir -p ~/books`
    - Edit `/etc/fstab` to add the mount configuration:
      ```
      LABEL=BOOKS /home/rpi/books auto defaults,nofail 0 0
      ```
    - Mount the storage: `sudo mount -a`.

### **Configure MPD**
13. Modify `/etc/mpd.conf` to specify the music directory and audio output:
    ```conf
    music_directory "/home/rpi/books"

    audio_output {
        type "alsa"
        name "My ALSA Device"
        device "default"
        mixer_control "PCM"
    }
    # Comment out `user` if enabled.
    ```

14. Restart MPD:
    ```bash
    sudo systemctl restart mpd
    sudo systemctl status mpd
    ```

### **Set Up Hardware and GPIO**
15. Add configurations for buttons and LEDs:
    ```bash
    echo "dtoverlay=gpio-shutdown" | sudo tee -a /boot/firmware/config.txt
    echo "gpio=4=op,pd,dh" | sudo tee -a /boot/firmware/config.txt
    ```

### **Configure Startup Scripts**
16. Set up a crontab to run your app script at startup:
    ```bash
    (sudo crontab -l; echo "@reboot /home/rpi/repo/bookplayer/online_light.py &") | sudo crontab -
    chmod +x /home/rpi/repo/bookplayer/online_light.py
    ```
