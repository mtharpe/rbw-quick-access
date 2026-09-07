# What is this???

Because of [this bug](https://github.com/doy/rbw/issues/11), getting passwords from `rbw` was painfully slow on macOS. Thankfully, someone made a [fork](https://github.com/Chr1s70ph/rbw) which solves this issue by batching decryption into a single round trip. They've created a [PR](https://github.com/doy/rbw/pull/359) into `doy/rbw`, but it's been months and has still not been merged.

Additionally, these custom builds of `rbw` bring in [this PR](https://github.com/doy/rbw/pull/315) which changed environment handling and made `rbw` as instantaneous as the Linux builds. Huge thanks to these two contributors for these fixes - without them, the macOS builds were going to be dead in the water.

This folder has two executables which I compiled from the fork: one for Apple Silicon-based Macs, and another for Intel-based Macs. These executables are loaded up and used only on these two architectures.
