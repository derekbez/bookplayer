#!/bin/bash

echo "*** Starting system update..."
sudo apt update && sudo apt upgrade -y
echo "*** System update completed."

echo "*** Installing Git..."
sudo apt install -y git
echo "*** Git installation completed."

echo "*** Configuring Git user details..."
git config --global user.name "derekbez"
git config --global user.email "derek@be-easy.com"
echo "*** Git configuration completed."

echo "*** Creating and activating a Python virtual environment 'repo'..."
python3 -m venv ~/repo
echo "source ~/repo/bin/activate" >> ~/.bashrc
echo "*** Virtual environment 'repo' will now activate automatically on new terminal sessions."
source ~/repo/bin/activate
cd repo
echo "*** Virtual environment 'repo' activated for the current session."

echo "*** Installing Python and essential packages..."
sudo apt install -y python3 python3-pip
sudo apt install -y python3-dev build-essential
sudo apt install -y python3-rpi-lgpio
sudo apt install -y python3-debugpy
sudo apt-get install sqlite3
echo "*** Python and essential packages installation completed."

echo "*** Ensuring pip is installed and updated..."
python -m ensurepip
python -m pip install --upgrade pip
echo "*** Pip is installed and updated."

echo "*** Installing GPIO and NFC-related packages..."
pip install RPi.GPIO
pip install nfcpy
sudo apt-get install -y libusb-1.0-0-dev libnfc-bin libnfc-dev libpcsclite-dev
echo "*** NFC-related packages installation completed."

echo "*** installing pytest..."
pip3 install pytest
pip3 install pytest-mock
echo "*** pytest install completed"

echo "*** Installing MPD and related tools..."
sudo apt-get install -y mpd
pip install python-mpd2
echo "*** MPD and related tools installation completed."

echo "*** Removing unnecessary packages..."
sudo apt autoremove -y
echo "*** Clean-up completed."

echo "*** Cloning the bookplayer repository..."
git clone https://github.com/derekbez/bookplayer.git bookplayer
echo "*** Repository cloned successfully."

echo "*** Setting up books folder and configuring fstab..."
sudo mkdir -p ~/books
sudo cp /etc/fstab /etc/fstab.bak
echo "*** Backup of /etc/fstab created."

echo "*** Adding mount point to fstab..."
echo "LABEL=BOOKS /home/rpi/books auto defaults,nofail 0 0" | sudo tee -a /etc/fstab
echo "*** Updated fstab file:"
cat /etc/fstab
echo "*** Mount point configuration completed."

echo "*** Configuring GPIO settings for power button and indicator light..."
echo "*** standby light..."
echo "dtoverlay=gpio-shutdown,gpio_pin=3" | sudo tee -a /boot/firmware/config.txt
echo "gpio=14=op,pd,dh" | sudo tee -a /boot/firmware/config.txt
echo "*** Updated /boot/firmware/config.txt:"
cat /boot/firmware/config.txt
echo "*** GPIO configuration completed."

echo "*** Setting up crontab for application startup..."
echo "*** Ready light..."
sudo crontab -l > crontab_backup.txt
(sudo crontab -l; echo "@reboot /home/rpi/repo/bookplayer/online_light.py &") | sudo crontab -
sudo crontab -l
chmod +x /home/rpi/repo/bookplayer/online_light.py
echo "*** Crontab setup completed."

echo "*** Configure MPD settings."
sudo cp /etc/mpd.conf /etc/mpd.conf.bak

# Update music directory
sudo sed -i 's|^music_directory.*|music_directory "/home/rpi/books"|' /etc/mpd.conf

# Ensure the correct playlist directory
sudo sed -i 's|^playlist_directory.*|playlist_directory "/var/lib/mpd/playlists"|' /etc/mpd.conf

# Update the database file location
sudo sed -i 's|^db_file.*|db_file "/var/lib/mpd/tag_cache"|' /etc/mpd.conf

# Ensure proper state tracking
sudo sed -i 's|^state_file.*|state_file "/var/lib/mpd/state"|' /etc/mpd.conf

# Remove user reference (if applicable)
sudo sed -i '/^user.*mpd/d' /etc/mpd.conf

# Set proper audio output settings
sudo tee -a /etc/mpd.conf > /dev/null <<EOL
audio_output {
    type            "alsa"
    name            "My ALSA Device"
    device          "default"
    mixer_control   "PCM"
}
EOL

# Start the mpd service
sudo systemctl enable mpd
sudo systemctl start mpd
sudo systemctl status mpd --no-pager
sudo apt-get install -y mpc



#
# BookPlayer systemd startup setup
#
echo "*** Creating systemd service for BookPlayer..."
sudo tee /etc/systemd/system/bookplayer.service > /dev/null <<EOL
[Unit]
Description=BookPlayer Application
After=mpd.service
Requires=mpd.service

[Service]
Type=simple
User=rpi
WorkingDirectory=/home/rpi/repo/bookplayer
ExecStart=/home/rpi/repo/bin/python /home/rpi/repo/bookplayer/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL

echo "*** Reloading systemd, enabling and starting BookPlayer service..."
sudo systemctl daemon-reload
sudo systemctl enable bookplayer
sudo systemctl start bookplayer
sudo systemctl status bookplayer --no-pager
echo "*** BookPlayer systemd service setup completed."


