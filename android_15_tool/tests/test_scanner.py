import os
import pytest
from android_15_tool.lib.scanner import MagicScanner

@pytest.fixture(scope="module")
def create_dummy_files(tmpdir_factory):
    """Creates a set of dummy files with different magic bytes for testing."""
    dummy_files = {}

    # Android Sparse
    fn_sparse = tmpdir_factory.mktemp("data").join("sparse.img")
    with open(fn_sparse, 'wb') as f:
        f.write(b'\x3A\xFF\x26\xED')
    dummy_files['Android Sparse'] = str(fn_sparse)

    # Super Partition
    fn_super = tmpdir_factory.mktemp("data").join("super.img")
    with open(fn_super, 'wb') as f:
        f.write(b'\x4C\x6B\x44\x61')
    dummy_files['Super Partition'] = str(fn_super)

    # Super Partition at offset 4096
    fn_super_4096 = tmpdir_factory.mktemp("data").join("super_4096.img")
    with open(fn_super_4096, 'wb') as f:
        f.write(b'\x00' * 4096)
        f.write(b'\x4C\x6B\x44\x61')
    dummy_files['Super Partition (Offset 4096)'] = str(fn_super_4096)

    # EROFS Filesystem
    fn_erofs = tmpdir_factory.mktemp("data").join("erofs.img")
    with open(fn_erofs, 'wb') as f:
        f.write(b'\x00' * 1024)
        f.write(b'\xE2\xE1\xF5\xE0')
    dummy_files['EROFS Filesystem'] = str(fn_erofs)

    # OTA Payload
    fn_payload = tmpdir_factory.mktemp("data").join("payload.bin")
    with open(fn_payload, 'wb') as f:
        f.write(b'PAYLOAD')
    dummy_files['OTA Payload'] = str(fn_payload)

    # Android Boot
    fn_boot = tmpdir_factory.mktemp("data").join("boot.img")
    with open(fn_boot, 'wb') as f:
        f.write(b'ANDROID!')
    dummy_files['Android Boot'] = str(fn_boot)

    # DTB
    fn_dtb = tmpdir_factory.mktemp("data").join("dtb.img")
    with open(fn_dtb, 'wb') as f:
        f.write(b'\x00' * 100)
        f.write(b'\xd0\x0d\xfe\xed')
    dummy_files['DTB'] = str(fn_dtb)

    # AVB 2.0 Footer
    fn_avb = tmpdir_factory.mktemp("data").join("avb.img")
    with open(fn_avb, 'wb') as f:
        f.write(b'\x00' * 70000)
        f.write(b'AVBb')
    dummy_files['AVB 2.0 Footer'] = str(fn_avb)

    # LZ4 Ramdisk
    fn_lz4 = tmpdir_factory.mktemp("data").join("lz4.img")
    with open(fn_lz4, 'wb') as f:
        f.write(b'\x00' * 50)
        f.write(b'\x04\x22\x4d\x18')
    dummy_files['LZ4 Ramdisk'] = str(fn_lz4)

    # DTC Table
    fn_dtc = tmpdir_factory.mktemp("data").join("dtc.img")
    with open(fn_dtc, 'wb') as f:
        f.write(b'\x00' * 200)
        f.write(b'TDBL')
    dummy_files['DTC Table'] = str(fn_dtc)

    # Unknown
    fn_unknown = tmpdir_factory.mktemp("data").join("unknown.img")
    with open(fn_unknown, 'wb') as f:
        f.write(b'UNKNOWN')
    dummy_files['Unknown'] = str(fn_unknown)

    return dummy_files

def test_magic_scanner(create_dummy_files):
    """
    Tests the MagicScanner against the dummy files.
    """
    scanner = MagicScanner()

    # Test each file type
    for file_type, file_path in create_dummy_files.items():
        result = scanner.identify_image(file_path)
        assert file_type in result
