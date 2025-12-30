import unittest
import os
import struct
import shutil
from android_15_tool.lib.boot_image import BootImage, _get_padded_size

class TestBootImageV2(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_output_boot_v2"
        os.makedirs(self.test_dir, exist_ok=True)
        self.boot_img_path = os.path.join(self.test_dir, "boot.img")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_dummy_boot_img(self, header_version, os_version):
        kernel_data = b'kernel_data'
        ramdisk_data = b'ramdisk_data'
        dtb_data = b'dtb_data'
        page_size = 4096

        header = struct.pack(
            '<8s9I',
            BootImage.BOOT_MAGIC,
            len(kernel_data),
            len(ramdisk_data),
            os_version,  # OS Version
            1024, # Header Size
            0, 0, 0, 0, # Reserved
            header_version # Header Version
        )
        cmdline = b'\x00' * BootImage.CMDLINE_SIZE
        dtb_size_field = struct.pack('<I', len(dtb_data))

        padded_header_size = _get_padded_size(len(header) + len(cmdline) + len(dtb_size_field), page_size)

        with open(self.boot_img_path, 'wb') as f:
            f.write(header)
            f.write(cmdline)
            f.write(dtb_size_field)
            f.seek(padded_header_size) # Seek past header
            f.write(kernel_data)
            f.seek(padded_header_size + _get_padded_size(len(kernel_data), page_size))
            f.write(ramdisk_data)
            f.seek(padded_header_size + _get_padded_size(len(kernel_data), page_size) + _get_padded_size(len(ramdisk_data), page_size))
            f.write(dtb_data)

    def test_unpack_android15_style_boot_img(self):
        """Test unpacking a boot.img with os_version=0 in the header."""
        # Arrange
        self.create_dummy_boot_img(header_version=4, os_version=0)
        boot_image = BootImage(self.boot_img_path)

        # Act
        boot_image.unpack(self.test_dir)

        # Assert
        header_info_path = os.path.join(self.test_dir, 'header_info.txt')
        self.assertTrue(os.path.exists(header_info_path))
        with open(header_info_path, 'r') as f:
            content = f.read()
            self.assertIn("os_version:0", content)
            self.assertIn("header_version:4", content)

if __name__ == '__main__':
    unittest.main()
