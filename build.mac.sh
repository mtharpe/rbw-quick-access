#!/bin/bash

# Keep track of the original directory
start_dir=$(pwd)

# maketmp, copy to the tmp dir, move to the src dir
dir=$(mktemp -d) && cp -r . $dir && cd $dir/src

# Copy the contents of style.qss into the contents between the two sentinels
sed -i '' \
    -e '/# STYLE_START/r style.qss' \
    -e '/# STYLE_START/,/# STYLE_END/{//! d;}' \
    main.py
# Finally we can just build..
../.venv/bin/pyinstaller --name rbw-quick-access main.py

# Copy over the artifacts
cd "$start_dir"
rm -rf ./build # Just in case
cp -r "$dir/src/dist/rbw-quick-access" ./build
# Delete our tmpdir for cleanliness
rm -rf $dir
# Copy the installation script to the build dir
cp install.mac.sh ./build
# Same goes for the platform-specific `rbw` build (mac only)
mkdir -p ./build/rbw/
cp "./rbw/$(arch)/rbw" ./build/rbw/
cp "./rbw/$(arch)/rbw-agent" ./build/rbw/
# A tiny bit more preprocessing
cd ./build
# And finally zip everything up for release.
zip -r ./build.zip ./_internal ./rbw-quick-access ./rbw ./install.mac.sh && cd ..

