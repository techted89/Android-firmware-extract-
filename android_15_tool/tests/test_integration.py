import os
import pytest
import subprocess
import sys
import struct
from unittest.mock import patch, MagicMock

# It's better to import the function and call it directly
from android_15_tool.main import main

def _get_padded_size(size, page_size):
    """Helper to calculate padded size, mirroring the main code."""
    return (size + page_size - 1) // page_size * page_size

# This fixture will mock the command-line tools called *by the application*,
# not the test process itself.
@pytest.fixture(autouse=True)
def mock_external_dependencies():
    """Mocks the external command-line tools."""
    with patch('shutil.which', return_value=True):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="mocked output", stderr="", returncode=0)
            yield mock_run

@pytest.fixture
def dummy_boot_image(tmpdir):
    """Creates a dummy boot.img file with correct padding."""
    boot_file = tmpdir.join("boot.img")
    page_size = 4096
    kernel_size = 4
    ramdisk_size = 4

    with open(boot_file, 'wb') as f:
        # Header
        header_data = [kernel_size, ramdisk_size, 0, 1648, 0, 0, 0, 0, 4]
        header = b'ANDROID!' + struct.pack('<9I', *header_data)
        f.write(header)
        f.write(b'\x00' * (page_size - len(header)))

        # Kernel and padding
        kernel_data = b'KERN'
        f.write(kernel_data)
        padded_kernel_size = _get_padded_size(kernel_size, page_size)
        f.write(b'\x00' * (padded_kernel_size - len(kernel_data)))

        # Ramdisk
        f.write(b'DISK')

    return str(boot_file)

@pytest.fixture
def dummy_repack_files(tmpdir):
    """Creates dummy kernel, ramdisk, and header files for repacking."""
    kernel_file = tmpdir.join("kernel")
    ramdisk_file = tmpdir.join("ramdisk")
    header_file = tmpdir.join("header_info.txt")

    with open(kernel_file, 'wb') as f:
        f.write(b"kernel_data")
    with open(ramdisk_file, 'wb') as f:
        f.write(b"ramdisk_data")
    with open(header_file, 'w') as f:
        f.write("header_version:4\n")
        f.write("header_size:1648\n")

    return {"kernel": str(kernel_file), "ramdisk": str(ramdisk_file), "header": str(header_file)}

def test_search_command(dummy_boot_image, monkeypatch, capsys):
    """Tests the 'search' command by calling main()."""
    monkeypatch.setattr(sys, 'argv', ["android-15-tool", "search", dummy_boot_image])
    main()
    captured = capsys.readouterr()
    assert "Android Boot" in captured.out

def test_extract_command(dummy_boot_image, monkeypatch, capsys):
    """Tests the 'extract' command by calling main()."""
    output_dir = os.path.join(os.path.dirname(dummy_boot_image), "extracted")
    monkeypatch.setattr(sys, 'argv', ["android-15-tool", "extract", dummy_boot_image, output_dir])
    main()
    captured = capsys.readouterr()
    assert "Handling as a boot/recovery image..." in captured.out
    assert os.path.exists(os.path.join(output_dir, "kernel"))
    assert os.path.exists(os.path.join(output_dir, "ramdisk"))
    assert os.path.exists(os.path.join(output_dir, "header_info.txt"))

def test_repack_command(dummy_repack_files, monkeypatch, capsys):
    """Tests the 'repack' command by calling main()."""
    output_image = os.path.join(os.path.dirname(dummy_repack_files["kernel"]), "new.img")
    monkeypatch.setattr(sys, 'argv', [
        "android-15-tool", "repack",
        "--header_info", dummy_repack_files["header"],
        "--kernel", dummy_repack_files["kernel"],
        "--ramdisk", dummy_repack_files["ramdisk"],
        "--cmdline", "console=ttyMSM0,115200n8",
        "--output", output_image
    ])
    main()
    captured = capsys.readouterr()
    assert f"Image repacked to {output_image}" in captured.out
    assert os.path.exists(output_image)

def test_dtc_decompile_command(tmpdir, monkeypatch, capsys):
    """Tests the 'dtc decompile' command by calling main()."""
    dtb_file = tmpdir.join("test.dtb")
    dts_file = tmpdir.join("test.dts")
    with open(dtb_file, 'wb') as f:
        f.write(b"dummy_dtb")

    monkeypatch.setattr(sys, 'argv', ["android-15-tool", "dtc", "decompile", str(dtb_file), str(dts_file)])
    main()
    captured = capsys.readouterr()
    assert f"Decompiled {dtb_file} to {dts_file}" in captured.out
