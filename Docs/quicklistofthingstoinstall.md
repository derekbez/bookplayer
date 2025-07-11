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
sudo apt install -y python3 python3-pip python3-dev build-essential python3-rpi-lgpio python3-debugpy sqlite3
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

echo "*** Installing pytest..."
pip3 install pytest pytest-mock
echo "*** pytest installation completed."

echo "*** Installing MPD and related tools..."
sudo apt-get install -y mpd mpc
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
echo "dtoverlay=gpio-shutdown,gpio_pin=3" | sudo tee -a /boot/firmware/config.txt
echo "gpio=14=op,pd,dh" | sudo tee -a /boot/firmware/config.txt
echo "*** Updated /boot/firmware/config.txt:"
cat /boot/firmware/config.txt
echo "*** GPIO configuration completed."

echo "*** Setting up crontab for application startup..."
sudo crontab -l > crontab_backup.txt
(sudo crontab -l; echo "@reboot /home/rpi/repo/bookplayer/online_light.py &") | sudo crontab -
chmod +x /home/rpi/repo/bookplayer/online_light.py
echo "*** Crontab setup completed."

echo "*** Configuring MPD settings..."
sudo cp /etc/mpd.conf /etc/mpd.conf.bak

# Update MPD configuration
sudo sed -i 's|^music_directory.*|music_directory "/home/rpi/books"|' /etc/mpd.conf
sudo sed -i 's|^playlist_directory.*|playlist_directory "/var/lib/mpd/playlists"|' /etc/mpd.conf
sudo sed -i 's|^db_file.*|db_file "/var/lib/mpd/tag_cache"|' /etc/mpd.conf
sudo sed -i 's|^state_file.*|state_file "/var/lib/mpd/state"|' /etc/mpd.conf
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

# Start MPD service
sudo systemctl enable mpd
sudo systemctl start mpd
sudo systemctl status mpd --no-pager

echo "*** Creating systemd service for BookPlayer..."
echo "*** Modifying systemd service for BookPlayer..."
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
KillMode=mixed
TimeoutStopSec=10s

[Install]
WantedBy=multi-user.target
EOL

echo "*** Reloading systemd, enabling and starting BookPlayer service..."
sudo systemctl daemon-reload
sudo systemctl enable bookplayer
sudo systemctl restart bookplayer
sudo systemctl status bookplayer --no-pager
echo "*** BookPlayer service updated successfully!"


echo "*** Configuring dhcpcd.conf for better network resilience..."
sudo tee -a /etc/dhcpcd.conf > /dev/null <<EOL
interface eth0
fallback static
noarp
EOL
echo "*** dhcpcd.conf modifications completed."

echo "*** Disabling NetworkManager-wait-online.service to prevent boot dependency..."
sudo systemctl disable NetworkManager-wait-online.service
echo "*** System will no longer wait for network during boot."

echo "*** Enabling journaling for filesystem protection..."
sudo tune2fs -O has_journal /dev/mmcblk0p2
echo "*** Journaling enabled for /dev/mmcblk0p2."

#echo "*** Disabling unnecessary services..."
#sudo systemctl disable bluetooth
#sudo systemctl disable triggerhappy
#echo "*** Unnecessary services disabled."

echo "*** Creating systemd service to unmount USB on shutdown..."
sudo tee /etc/systemd/system/unmount-usb.service > /dev/null <<EOL
[Unit]
Description=Unmount USB on shutdown
DefaultDependencies=no
Before=shutdown.target

[Service]
Type=oneshot
ExecStart=/bin/umount /dev/sda1

[Install]
WantedBy=shutdown.target
EOL

echo "*** Enabling automatic USB unmount service..."
sudo systemctl daemon-reload
sudo systemctl enable unmount-usb

echo "*** Installation complete! Please reboot the system to apply changes."
