#!/bin/bash

# maketmp, copy to the tmp dir, move to the src dir
dir=$(mktemp -d) && cp -r . $dir && cd $dir/src
# Copy the contents of style.qss into the contents between the two sentinels
sed -i \
    -e '/# STYLE_START/r style.qss' \
    -e '/# STYLE_START/,/# STYLE_END/{//!d}' \
    main.py
# Finally we can just build..
../.venv/bin/pyinstaller main.py
