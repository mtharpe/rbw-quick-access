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

echo "Installed to $INSTALL_DIR with a symlink in /usr/local/bin"