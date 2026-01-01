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
python3 -m android_15_tool extract <file> <output_dir>
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
