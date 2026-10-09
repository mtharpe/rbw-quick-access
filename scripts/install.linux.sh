#!/bin/bash

if [ "$EUID" -eq 0 ]; then 
    echo "Do not run this script as root! Elevated commands will ask you for your password when necessary"
    exit 1
fi

DOWNLOAD_DIR="$(mktemp -d)"

download() {
    echo -n "Downloading latest release of rbw-quick-access from git..."

    latest_endpoint="https://git.forgeserv.cloud/api/v1/repos/oitsjustjose/rbw-quick-access/releases/latest"

    if ! command -v jq > /dev/null 2>&1; then
        echo "`jq` not found!"
        return 1
    fi

    if command -v curl > /dev/null 2>&1; then
        data=$(curl -s $latest_endpoint)
    elif command -v wget > /dev/null 2>&1; then
        data=$(wget $latest_endpoint)
    fi

    if [[ -z $data ]]; then
        echo "Failed to download the latest release, please install manually!"
        return 1
    fi

    # Get the release name, filtering by "Linux"
    rel_name=$(echo $data | jq .assets[] | jq .name | grep -i linux)
    # Finally filter down to get the actual URI
    dl_url=$(echo $data | jq .assets[] | jq "select(.name == $rel_name)" | jq -r .browser_download_url)

    # Which we can use to download the file
    if command -v curl > /dev/null 2>&1; then
        curl -s -o "$DOWNLOAD_DIR/rbw-quick-access.tar.gz" "$dl_url"
    elif command -v wget > /dev/null 2>&1; then
        wget -O "$DOWNLOAD_DIR/rbw-quick-access.tar.gz" "$dl_url"
    fi

    echo "      Done!"
    return 0
}

install() {
    INSTALL_DIR="/opt/rbw-quick-access"

    sudo pkill -9 rbw-quick-acces
    # Clean up the old install
    sudo rm -rf "$INSTALL_DIR"
    sudo rm -f /usr/local/bin/rbw-quick-access

    # Make `/opt` dir, copy things over to it
    sudo mkdir -p "$INSTALL_DIR"

    echo -n "Extracting and copying files..."
    sh -c "cd $DOWNLOAD_DIR && tar -xzvf rbw-quick-access.tar.gz > /dev/null 2>&1"
    sudo cp -a "$DOWNLOAD_DIR/rbw-quick-access/rbw-quick-access" "$INSTALL_DIR"
    sudo cp -a "$DOWNLOAD_DIR/rbw-quick-access/_internal" "$INSTALL_DIR"
    # Finally make a symlink to the `/opt` exec in /usr/local/bin
    sudo ln -sf "$INSTALL_DIR/rbw-quick-access" /usr/local/bin/rbw-quick-access
    echo "      Done!"
    
    return 0
}

register_init() {    
    # Sets up the respective runit/systemd/openrc service

    systemd() {
        if ! command -v systemctl > /dev/null 2>&1; then
            return 1
        fi

        service='[Unit]\nDescription=rbw quick access background service\nAfter=network.target\nStartLimitIntervalSec=0\n\n[Service]\nType=simple\nRestart=always\nRestartSec=1\nExecStart=/usr/local/bin/rbw-quick-access\n\n[Install]\nWantedBy=default.target\n'
        # Save the above service to a file
        printf "$service" | sudo tee /etc/systemd/user/rbw-quick-access.service > /dev/null
        # Enable the service for the user
        systemctl --user enable rbw-quick-access.service
        # Start the service for the user - use restart that way if it exists already, it works too.
        systemctl --user restart rbw-quick-access.service

        echo "systemd service configured and started!"
        return 0
    }

    openrc() {
        if ! command -v rc-service > /dev/null 2>&1; then
            return 1
        fi

        service='#!/sbin/openrc-run\n\nname="rbw-quick-access"\ndescription="Quick access background service for RBW"\n\ncommand="/usr/local/bin/rbw-quick-access"\n\ndepend() {\n    need net\n}\n\nstart() {\n    echo "Starting RBW quick access..."\n    /usr/local/bin/rbw-quick-access &\n    echo $! > /var/run/${name}.pid\n}\n\nstop() {\n    kill -9 `cat /var/run/${name}.pid`\n    echo "Stopping RBW quick access..."\n}'
        # Save the above service to an initrc file
        printf "$service" | sudo tee /etc/systemd/user/rbw-quick-access.service > /dev/null
        # Install the service
        sudo rc-update add rbw-quick-access default
        # And finally start - use restart that way if it exists already, it works too.
        sudo rc-service rbw-quick-access restart

        echo "openrc entry created and service started!"
        return 0
    }

    runit() {
        if ! command -v sv > /dev/null 2>&1; then
            return 1
        fi

        # Prep the service dir
        sudo mkdir -p /var/service/rbw-quick-access
        # Set up run and status scripts (flattened for my sanity)
        run_script='#!/bin/sh\n/usr/local/bin/rbw-quick-access &\n# Important: Ensure the process is backgrounded and PID is managed\necho $! > /var/run/rbw-quick-access.pid\nexit 0'
        status_script='#!/bin/sh\n# Check if the PID file exists and the process is running\nPID=$(cat /var/run/rbw-quick-access.pid)\nif kill -0 $PID 2>/dev/null; then\n    exit 0 # Running\nelse\n    exit 1 # Not running\nfi'
        # And save them to the service dir
        printf "$run_script" | sudo tee /var/service/rbw-quick-access/run > /dev/null
        printf "$status_script" | sudo tee /var/service/rbw-quick-access/status > /dev/null
        # Finally we can spin up the service
        sudo sv up /var/service/rbw-quick-access

        echo "runit service made at /var/service/rbw-quick-access and has been started!"
        return 0
    }


    fallback() {
        echo "Installed to /usr/local/bin/rbw-quick-access"
        echo "  - ⚠️  You will need to configure the application to start on startup yourself ⚠️"
    }

    finalize() {
        # Check if we're already in the `input` user group, add to group if not
        if [ -z "$(getent group | grep -i "$USER" | grep -i input)" ]; then
            sudo usermod -aG input "$USER"
            echo "User $USER has been added to the 'input' group - a system restart will be required!"
        fi
    }

    !(systemd || openrc || runit) && fallback
    
    finalize    
    return 0
}

download && install && register_init && echo "Installation complete!"

