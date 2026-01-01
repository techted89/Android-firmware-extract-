import os
import shutil
import glob

from android_15_tool.lib.boot_image import BootImage
from android_15_tool.lib.super_unpacker import SuperUnpacker
from android_15_tool.lib.unsparse import SparseImage
from android_15_tool.lib.twrp_device_tree import create_twrp_device_tree


class DeviceTreeBuilder:
    """
    Orchestrates the process of building a TWRP device tree from firmware files.
    """

    def __init__(self, firmware_dir, output_dir):
        self.firmware_dir = firmware_dir
        self.output_dir = output_dir
        self.temp_dir = os.path.join(output_dir, "temp")
        self.device_tree_dir = os.path.join(output_dir, "device_tree")
        self.firmware_files = {}

    def build(self):
        """
        Executes the full device tree building process.
        """
        print("Starting TWRP device tree build process...")
        self._setup_directories()
        self._discover_firmware_files()
        self._combine_sparse_chunks()
        self._extract_and_assemble()

        if "super" in self.firmware_files:
            create_twrp_device_tree(self.firmware_files["super"], self.device_tree_dir)
        else:
            print("Warning: super.img not found, skipping BoardConfig.mk generation.")

        print(f"Device tree build process complete. Output at: {self.device_tree_dir}")

    def _setup_directories(self):
        """
        Creates the necessary output and temporary directories.
        """
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        if not os.path.exists(self.device_tree_dir):
            os.makedirs(self.device_tree_dir)

    def _discover_firmware_files(self):
        """
        Scans the firmware directory to find all relevant firmware files.
        """
        print("Discovering firmware files...")
        for file in os.listdir(self.firmware_dir):
            if file.startswith("super.img_sparsechunk"):
                if "super_sparse" not in self.firmware_files:
                    self.firmware_files["super_sparse"] = []
                self.firmware_files["super_sparse"].append(os.path.join(self.firmware_dir, file))
            elif file.endswith(".img"):
                name = os.path.splitext(file)[0]
                self.firmware_files[name] = os.path.join(self.firmware_dir, file)

        # Sort sparse chunks to ensure correct order
        if "super_sparse" in self.firmware_files:
            self.firmware_files["super_sparse"].sort()

    def _extract_and_assemble(self):
        """
        Extracts firmware images and assembles the device tree.
        """
        print("Extracting and assembling device tree...")
        for name, path in self.firmware_files.items():
            if name == "super":
                self._extract_super(path)
            elif name in ["boot", "vendor_boot", "recovery", "init_boot"]:
                self._extract_boot(path)

    def _extract_super(self, super_img_path):
        """
        Extracts the super.img file and copies fstab files.
        """
        print(f"Extracting {super_img_path}...")
        super_out_dir = os.path.join(self.temp_dir, "super")
        unpacker = SuperUnpacker(super_img_path)
        unpacker.unpack(super_out_dir)

        for partition_img in os.listdir(super_out_dir):
            if partition_img.endswith(".img") and "fstab" in partition_img:
                shutil.copy(
                    os.path.join(super_out_dir, partition_img),
                    os.path.join(self.device_tree_dir, partition_img)
                )

    def _extract_boot(self, boot_img_path):
        """
        Extracts a boot/recovery image and copies key components.
        """
        print(f"Extracting {boot_img_path}...")
        boot_out_dir = os.path.join(self.temp_dir, os.path.basename(boot_img_path))
        boot_image = BootImage(boot_img_path)
        boot_image.unpack(boot_out_dir)

        for item in ["kernel", "ramdisk", "dtb"]:
            item_path = os.path.join(boot_out_dir, item)
            if os.path.exists(item_path):
                shutil.copy(item_path, self.device_tree_dir)

    def _combine_sparse_chunks(self):
        """
        Combines sparse super.img chunks into a single raw image file.
        """
        if "super_sparse" not in self.firmware_files:
            return

        print("Combining sparse super.img chunks...")
        raw_super_path = os.path.join(self.temp_dir, "super.img")

        # Use the unsparse tool to combine the chunks
        sparse_image = SparseImage(self.firmware_files["super_sparse"][0])
        sparse_image.unsparse(raw_super_path)

        self.firmware_files["super"] = raw_super_path
