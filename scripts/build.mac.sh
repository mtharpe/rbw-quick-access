#!/bin/bash

# Validate that the version arg is provided
if [ -z "$1" ]; then
    echo "Missing required positional argument: <version>"
    exit 1
fi

version="$1"

for arch in arm64 x86_64; do
    echo "Building for $arch..."
    artifact_name="rbw-quick-access-macos-${arch}_${version}.tar.gz"

    python -m PyInstaller \
        --target-arch "$arch" \
        --workpath "build/$arch/work" \
        --distpath "build/$arch/dist" \
        --specpath "build/$arch/spec" \
        --name rbw-quick-access \
        src/main.py 2>&1

    # Copy the installation script to the build dir
    #  this includes our special `rbw` build
    cp scripts/install.mac.sh "build/$arch/dist/rbw-quick-access"
    cp -r "./rbw/$arch" "build/$arch/dist/rbw-quick-access/rbw"
    # And finally tar everything up for release. We `cd` into
    #  build to avoid the untar'd path to start with build/
    echo "tarring build/$arch/dist/rbw-quick-access to $artifact_name"
    tar -zcvf $artifact_name -C "build/$arch/dist" rbw-quick-access 
done

