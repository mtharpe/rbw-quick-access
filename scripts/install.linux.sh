#!/bin/bash

if [ "$EUID" -eq 0 ]; then 
    echo "Do not run this script as root! Elevated commands will ask you for your password when necessary"
    exit 1
fi

INSTALL_DIR="/opt/rbw-quick-access"
echo "Installing to $INSTALL_DIR..."

sudo pkill -9 rbw-quick-acces
# Clean up the old install
sudo rm -rf "$INSTALL_DIR"
sudo rm -f /usr/local/bin/rbw-quick-access

# Make `/opt` dir, copy things over to it
sudo mkdir -p "$INSTALL_DIR"

echo "Copying files.."
sudo cp -a ./rbw-quick-access "$INSTALL_DIR"
sudo cp -a ./_internal "$INSTALL_DIR"

# Finally make a symlink to the `/opt` exec in /usr/local/bin
sudo ln -sf "$INSTALL_DIR/rbw-quick-access" /usr/local/bin/rbw-quick-access

if command -v systemctl >/dev/null 2>&1; then
    service="
[Unit]
Description=rbw quick access background service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
ExecStart=/usr/local/bin/rbw-quick-access

[Install]
WantedBy=default.target
"
    # Save the above service to a file
    printf "$service" | sudo tee /etc/systemd/user/rbw-quick-access.service > /dev/null
    # Enable the service for the user
    systemctl --user enable rbw-quick-access.service
    # Start the service for the user - use restart that way if it exists already, it works too.
    systemctl --user restart rbw-quick-access.service
    # Check if we're already in the `input` user group
    if [ -z "$(getent group | grep -i "$USER" | grep -i input)" ]; then
        sudo usermod -aG input "$USER"
        echo "User $USER has been added to the 'input' group - a system restart will be required!"
    else
        echo "rbw-quick-access has been installed/updated!"
    fi
else
    bash -c "nohup rbw-quick-access >/dev/null 2>&1  &"

    echo "Installed to /usr/local/bin/rbw-quick-access"
    echo "  - The application has already started for you - show with [Super]+[Shift]+[\]"
    echo "  - ⚠️  You will need to configure the application to start on startup yourself ⚠️"
fi
