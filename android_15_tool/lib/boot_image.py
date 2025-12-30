import struct
import os

def _get_padded_size(size, page_size):
    """Calculates the size padded to the page size."""
    return (size + page_size - 1) // page_size * page_size

class BootImage:
    """
    Parses boot.img and recovery.img files (v3/v4).
    """

    BOOT_MAGIC = b'ANDROID!'
    BOOT_ARGS_SIZE = 512
    BOOT_EXTRA_ARGS_SIZE = 1024
    CMDLINE_SIZE = BOOT_ARGS_SIZE + BOOT_EXTRA_ARGS_SIZE

    def __init__(self, filepath, page_size=4096):
        self.filepath = filepath
        self.page_size = page_size
        self.header = None
        self.kernel = None
        self.ramdisk = None
        self.dtb = None

    def _parse_header(self, f):
        """
        Parses the boot image header (v3/v4).
        """
        f.seek(0)
        magic = f.read(len(self.BOOT_MAGIC))
        if magic != self.BOOT_MAGIC:
            raise ValueError("Invalid boot image: incorrect magic.")

        # Read the main part of the header (up to header_version)
        header_v3_v4_bin = f.read(36)
        if len(header_v3_v4_bin) < 36:
            raise ValueError("Invalid boot image header: too short.")

        header_data = struct.unpack('<9I', header_v3_v4_bin)

        self.header = {
            'kernel_size': header_data[0],
            'ramdisk_size': header_data[1],
            'os_version': header_data[2],
            'header_size': header_data[3],
            'header_version': header_data[8],
            'dtb_size': 0,
        }

        if self.header['header_version'] >= 4:
            # For v4, the dtb_size is after the cmdline
            f.seek(len(self.BOOT_MAGIC) + 36 + self.CMDLINE_SIZE)
            dtb_size_bin = f.read(4)
            if len(dtb_size_bin) < 4:
                raise ValueError("Could not read dtb_size for v4 header.")
            self.header['dtb_size'] = struct.unpack('<I', dtb_size_bin)[0]

        # Calculate padded sizes
        padded_kernel_size = _get_padded_size(self.header['kernel_size'], self.page_size)
        padded_ramdisk_size = _get_padded_size(self.header['ramdisk_size'], self.page_size)

        # Calculate offsets
        kernel_offset = self.page_size
        ramdisk_offset = kernel_offset + padded_kernel_size
        dtb_offset = ramdisk_offset + padded_ramdisk_size

        # Read kernel
        f.seek(kernel_offset)
        self.kernel = f.read(self.header['kernel_size'])

        # Read ramdisk
        f.seek(ramdisk_offset)
        self.ramdisk = f.read(self.header['ramdisk_size'])

        # Read DTB if it exists
        if self.header['header_version'] >= 4 and self.header['dtb_size'] > 0:
            f.seek(dtb_offset)
            self.dtb = f.read(self.header['dtb_size'])

        # For Android 15+, os_version might be in AVB footer
        if self.header['os_version'] == 0:
            # Placeholder for AVB footer parsing logic
            # This would involve finding and parsing the AVB metadata
            self.header['avb_os_version'] = "parsed_from_avb"
            self.header['avb_security_patch'] = "parsed_from_avb"


    def unpack(self, output_dir):
        """
        Extracts the kernel, ramdisk, and DTB to the output directory.
        """
        try:
            with open(self.filepath, 'rb') as f:
                self._parse_header(f)

            if self.kernel:
                with open(os.path.join(output_dir, 'kernel'), 'wb') as f:
                    f.write(self.kernel)
            if self.ramdisk:
                with open(os.path.join(output_dir, 'ramdisk'), 'wb') as f:
                    f.write(self.ramdisk)
            if self.dtb:
                with open(os.path.join(output_dir, 'dtb'), 'wb') as f:
                    f.write(self.dtb)

            # Save header info for repacking
            with open(os.path.join(output_dir, 'header_info.txt'), 'w') as f:
                for key, value in self.header.items():
                    f.write(f"{key}:{value}\n")

        except (ValueError, struct.error) as e:
            raise RuntimeError(f"Error processing boot image: {e}")
        except FileNotFoundError:
            raise RuntimeError(f"Input file not found: {self.filepath}")
        except IOError as e:
            raise RuntimeError(f"I/O error: {e}")
