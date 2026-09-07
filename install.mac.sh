#!/bin/bash
# Assert root
if [ "$EUID" -ne 0 ]
  then echo "Please run this script with root permissions!"
  exit
fi


INSTALL_DIR="/opt/rbw-quick-access"
echo "Installing to $INSTALL_DIR..."

# Make `/opt` dir, copy things over to it
mkdir -p "$INSTALL_DIR"

echo "Copying files.."
cp ./rbw-quick-access "$INSTALL_DIR"
cp -r ./rbw/rbw "$INSTALL_DIR"
cp -r ./rbw/rbw-agent "$INSTALL_DIR"
cp -r ./_internal "$INSTALL_DIR"

# Finally make a symlink to the `/opt` exec in /usr/local/bin
ln -sf "$INSTALL_DIR/rbw-quick-access" /usr/local/bin/rbw-quick-access

echo "Installed!"