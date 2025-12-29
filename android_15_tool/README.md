# Android 15 Firmware and Recovery Tool

This is a command-line tool for extracting and repacking Android 15 firmware and recovery images. It is designed to be a low-level binary extraction tool that can handle the complexities of modern Android firmware.

## Features

*   **Image Identification:** The tool can identify various Android image types, including:
    *   Android Sparse Images (`system.img`, `vendor.img`, etc.)
    *   Super Partitions (`super.img`)
    *   EROFS Filesystems
    *   OTA Payloads (`payload.bin`)
    *   Boot and Recovery Images (`boot.img`, `recovery.img`)
    *   Device Tree Blobs (DTBs)
*   **Firmware Extraction:** The tool can extract the contents of these images, including:
    *   Un-sparsing sparse images to raw images.
    *   Extracting EROFS filesystems.
    *   Unpacking boot and recovery images into their components (kernel, ramdisk, DTB).
*   **Recovery and DTB Handling:** The tool can decompile and recompile Device Tree Blobs, which is essential for modifying and rebuilding custom recovery images.
*   **Repacking:** The tool can repack boot and recovery images, preserving the original header information to ensure that the repacked image is a drop-in replacement.

## Installation

To install the tool, clone this repository and install it in editable mode:

```bash
git clone <repository-url>
cd android_15_tool
pip install -e .
```

## Usage

The tool is used via the `android-15-tool` command-line interface. The following commands are available:

*   `search`: Search for magic signatures in a file.
*   `extract`: Extract a firmware or recovery image.
*   `repack`: Repack a boot/recovery image.
*   `dtc`: Decompile or recompile a Device Tree Blob.

For more detailed information on each command, use the `--help` flag. For example:

```bash
android-15-tool extract --help
```

## Disclaimer

This tool is designed for advanced users who are familiar with the Android build system and firmware structure. Modifying and flashing firmware can be a risky process, and this tool is provided as-is with no warranty. Always be sure to back up your data before making any changes to your device.
