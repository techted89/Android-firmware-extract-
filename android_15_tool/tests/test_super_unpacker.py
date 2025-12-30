import pytest
import os
import struct

from android_15_tool.lib.super_unpacker import SuperUnpacker

SUPER_IMG_FILE = "super.img"


@pytest.fixture
def dummy_super_img():
    """Create a dummy super.img file with valid geometry and metadata."""
    with open(SUPER_IMG_FILE, "wb") as f:
        # 1. Write LpMetadataGeometry
        geometry = struct.pack(
            '<II32sIII',
            SuperUnpacker.LP_METADATA_GEOMETRY_MAGIC,
            52,  # struct_size
            b'\x00' * 32,  # checksum
            65536,  # metadata_max_size
            1,  # metadata_slot_count
            4096,  # logical_block_size
        )
        f.seek(4096)
        f.write(geometry)

        # 2. Write LpMetadataHeader
        slot_offset = 8192
        partitions_size = 2 * 52  # 2 partitions, 52 bytes each
        header_size = SuperUnpacker.LP_METADATA_HEADER_MIN_SIZE
        header = struct.pack(
            '<IHH I 32s I 32s I 32s I 32s',
            SuperUnpacker.LP_METADATA_HEADER_MAGIC,
            1, 0,  # version
            header_size,
            b'\x00' * 32,  # header_checksum
            partitions_size,
            b'\x00' * 32,  # partitions_checksum
            0, b'\x00' * 32,  # extents
            0, b'\x00' * 32,  # groups
        )
        f.seek(slot_offset)
        f.write(header)

        # 3. Write Partition Table Entries
        f.seek(slot_offset + header_size)
        system_part = b'system'.ljust(36, b'\x00')
        vendor_part = b'vendor'.ljust(36, b'\x00')
        part1 = struct.pack('<36sIIII', system_part, 0, 0, 1, 0)
        part2 = struct.pack('<36sIIII', vendor_part, 0, 1, 1, 0)
        f.write(part1)
        f.write(part2)

    yield SUPER_IMG_FILE
    os.remove(SUPER_IMG_FILE)


def test_super_unpacker_parse_metadata(dummy_super_img):
    """Test that the SuperUnpacker can parse the metadata."""
    unpacker = SuperUnpacker(dummy_super_img)
    with open(dummy_super_img, "rb") as f:
        unpacker._parse_metadata(f)

    assert unpacker.metadata is not None
    assert len(unpacker.metadata["partitions"]) == 2
    assert unpacker.metadata["partitions"][0]["name"] == "system"
    assert unpacker.metadata["partitions"][1]["name"] == "vendor"
