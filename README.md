# Android 15 Firmware and Recovery Tool

A command-line tool for working with Android 15 firmware and recovery images.

## Features

*   **Search:** Scan a file for Android-specific magic signatures (`boot.img`, `super.img`, etc.).
*   **Extract:** Unpack sparse images, EROFS filesystems, and boot/recovery images.
*   **Repack:** Re-create a `boot.img` or `recovery.img` from its components.
*   **DTC:** Decompile and compile Device Tree Blobs (.dtb/.dts).
*   **Dump:** Dump partitions from a rooted Android device using `adb`.

## Usage

### Search
```bash
python3 -m android_15_tool search <file>
```

### Extract
```bash
python3 -m android_15_tool extract <file> <output_dir> [--partitions <partition1>,<partition2>,...]
```

### Repack
```bash
python3 -m android_15_tool repack --header_info <header_info.txt> --kernel <kernel> --ramdisk <ramdisk> --output <new_image.img>
```

### DTC
```bash
python3 -m android_15_tool dtc decompile <input.dtb> <output.dts>
python3 -m android_15_tool dtc compile <input.dts> <output.dtb>
```

### Dump
```bash
python3 -m android_15_tool dump <partition_name> <output_dir>
```

### TWRP Tree
```bash
python3 -m android_15_tool twrp-tree <super.img> <output_dir>
```

### Build TWRP Tree
```bash
python3 -m android_15_tool build-twrp-tree <firmware_dir> <output_dir>
```
This command automates the entire process of creating a TWRP device tree. It discovers firmware files, combines sparse chunks, extracts partitions and their filesystems, and merges them into a unified `root` directory.

The tool then intelligently analyzes the extracted filesystem to:
1.  **Detect the Android version** and generate a `build_twrp.sh` script that automatically selects the correct TWRP source branch for the build.
2.  **Generate a `proprietary-files.txt` manifest** by scanning for common vendor files.
3.  **Create an `extract-files.sh` script** that uses the manifest to copy all necessary vendor blobs into the device tree.

The final output is a nearly complete, buildable TWRP device tree with an automated build script. Simply run `build_twrp.sh` to start the TWRP build process.
