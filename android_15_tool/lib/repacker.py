import struct
import os
import subprocess
import shutil

def _get_padded_size(size, page_size):
    """Calculates the size padded to the page size."""
    return (size + page_size - 1) // page_size * page_size

class Repacker:
    """
    Repacks boot and recovery images.
    """

    BOOT_MAGIC = b'ANDROID!'
    BOOT_ARGS_SIZE = 512
    BOOT_EXTRA_ARGS_SIZE = 1024
    CMDLINE_SIZE = BOOT_ARGS_SIZE + BOOT_EXTRA_ARGS_SIZE

    def __init__(self, output_path="new_boot.img"):
        self.output_path = output_path
        self._check_for_avbtool()

    def _check_for_avbtool(self):
        """
        Checks if avbtool is installed.
        """
        if not shutil.which("avbtool"):
            print("Warning: avbtool not found. AVB signing will be skipped.")

    def _read_header_info(self, header_info_path):
        """
        Reads the header info from the file saved during unpacking.
        """
        header_info = {}
        with open(header_info_path, 'r') as f:
            for line in f:
                key, value = line.strip().split(':', 1)
                header_info[key] = int(value)
        return header_info

    def repack(self, header_info_path, kernel_path, ramdisk_path, dtb_path=None, cmdline="", page_size=4096):
        """
        Repacks the image using the original header info.
        """
        header_info = self._read_header_info(header_info_path)

        kernel_size = os.path.getsize(kernel_path)
        ramdisk_size = os.path.getsize(ramdisk_path)
        dtb_size = os.path.getsize(dtb_path) if dtb_path else 0

        # Create the main header
        header = struct.pack(
            '<8s9I',
            self.BOOT_MAGIC,
            kernel_size,
            ramdisk_size,
            header_info.get('os_version', 0),
            header_info.get('header_size', 1648),
            0, 0, 0, 0, # reserved
            header_info.get('header_version', 4)
        )

        # Pack cmdline
        cmdline_bytes = cmdline.encode('utf-8')
        cmdline_padded = cmdline_bytes + b'\x00' * (self.CMDLINE_SIZE - len(cmdline_bytes))

        with open(self.output_path, 'wb') as f:
            # Write header, cmdline, and padding
            f.write(header)
            f.write(cmdline_padded)

            if header_info.get('header_version', 4) >= 4:
                f.write(struct.pack('<I', dtb_size))

            # Pad to the first page
            current_size = f.tell()
            f.write(b'\x00' * (page_size - current_size))

            # Write kernel and padding
            with open(kernel_path, 'rb') as k:
                f.write(k.read())
            f.write(b'\x00' * (_get_padded_size(kernel_size, page_size) - kernel_size))

            # Write ramdisk and padding
            with open(ramdisk_path, 'rb') as r:
                f.write(r.read())
            f.write(b'\x00' * (_get_padded_size(ramdisk_size, page_size) - ramdisk_size))

            # Write dtb and padding
            if dtb_path:
                with open(dtb_path, 'rb') as d:
                    f.write(d.read())
                f.write(b'\x00' * (_get_padded_size(dtb_size, page_size) - dtb_size))

    def sign_with_avb(self, key_path):
        """
        Signs the image with AVB (placeholder).
        """
        if not shutil.which("avbtool"):
            raise EnvironmentError("avbtool not found.")
        print(f"Placeholder for AVB signing with key: {key_path}")
