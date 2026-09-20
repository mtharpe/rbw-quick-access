#!/bin/bash

pinentry="$(brew --prefix)/bin/pinentry-mac"

if [ ! -f "$pinentry" ]; then
    echo "Installing pinentry-mac"
    brew install pinentry-mac
fi

echo "Configuring rbw to use pinentry-mac"
./rbw/rbw config set pinentry "$pinentry"

INSTALL_DIR="/opt/rbw-quick-access"
echo "Installing to $INSTALL_DIR..."

# Clean up the old install
pkill -9 rbw rbw-agent rbw-quick-access
sudo rm -rf "$INSTALL_DIR"
sudo rm -f /usr/local/bin/rbw-quick-access

# Make `/opt` dir, copy things over to it
sudo mkdir -p "$INSTALL_DIR"

echo "Copying files.."
sudo cp -a ./rbw-quick-access "$INSTALL_DIR"
sudo cp -a ./_internal "$INSTALL_DIR"
# These two live in /usr/local/bin that way they're already in $PATH
#  (since `rbw` relies on being able to contact `rbw-agent` from $PATH)
sudo cp -a ./rbw/rbw /usr/local/bin/
sudo cp -a ./rbw/rbw-agent /usr/local/bin/

# Finally make a symlink to the `/opt` exec in /usr/local/bin
sudo ln -sf "$INSTALL_DIR/rbw-quick-access" /usr/local/bin/rbw-quick-access

# Clean up the old rbw quick access startup script
osascript -e \
    'tell application "System Events" to delete login item "rbw-quick-access"' \
    2>/dev/null || true

read -p "Should rbw-quick-access start on login? y/n" -n 1 -r


if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add rbw-quick-access as a login item
    LAUNCH_AGENT="$HOME/Library/LaunchAgents/com.oitsjustjose.rbw-quick-access.plist"
    mkdir -p "$HOME/Library/LaunchAgents"
    cat > "$LAUNCH_AGENT" <<-EOF
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.oitsjustjose.rbw-quick-access</string>

        <key>ProgramArguments</key>
        <array>
            <string>/usr/local/bin/rbw-quick-access</string>
        </array>

        <key>RunAtLoad</key>
        <true/>

        <key>KeepAlive</key>
        <true/>

        <key>ProcessType</key>
        <string>Interactive</string>
    </dict>
    </plist>
EOF
    launchctl bootstrap "gui/$(id -u)" "$LAUNCH_AGENT"
else
    bash -c "nohup rbw-quick-access >/dev/null 2>&1  &"
fi

echo "Installed to $INSTALL_DIR with a symlink in /usr/local/bin"
echo " Give it a try with CMD+Shift+\\!"