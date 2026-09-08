#!/bin/bash

# Validate that the version arg is provided
if [ -z "$1" ]; then
    echo "Missing required positional argument: <version>"
    exit 1
fi

version="$1"
dist_dir=build/dist/rbw-quick-access
artifact_name="rbw-quick-access-macos-$(arch)_$version.tar.gz"

python -m PyInstaller \
    --workpath "build/work" \
    --distpath "build/dist" \
    --specpath "build/spec" \
    --name rbw-quick-access \
    src/main.py

# Copy the installation script to the build dir
#  this includes our special `rbw` build
cp scripts/install.mac.sh build/dist/rbw-quick-access
cp -r "./rbw/$(arch)" build/dist/rbw-quick-access/rbw
# And finally tar everything up for release. We `cd` into
#  build to avoid the untar'd path to start with build/
tar -zcvf $artifact_name -C build/dist rbw-quick-access 
