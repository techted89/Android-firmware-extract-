import os
import pytest
import struct
from android_15_tool.lib.unsparse import SparseImage

@pytest.fixture
def dummy_sparse_image(tmpdir):
    """Creates a dummy sparse image file for testing."""
    sparse_file = tmpdir.join("sparse.img")

    # Header
    header = {
        'magic': 0xed26ff3a,
        'major_version': 1,
        'minor_version': 0,
        'file_hdr_sz': 28,
        'chunk_hdr_sz': 12,
        'blk_sz': 4096,
        'total_blks': 3,
        'total_chunks': 2,
        'image_checksum': 0,
    }
    header_bin = struct.pack('<I4H4I', *header.values())

    # Chunk 1: RAW
    chunk1_header = {
        'type': 0xCAC1,
        'reserved1': 0,
        'chunk_sz': 1,
        'total_sz': 12 + 4096,
    }
    chunk1_header_bin = struct.pack('<2H2I', *chunk1_header.values())
    chunk1_data = b'A' * 4096

    # Chunk 2: FILL
    chunk2_header = {
        'type': 0xCAC2,
        'reserved1': 0,
        'chunk_sz': 2,
        'total_sz': 12 + 4,
    }
    chunk2_header_bin = struct.pack('<2H2I', *chunk2_header.values())
    chunk2_data = struct.pack('<I', 0xBBBBBBBB)

    with open(sparse_file, 'wb') as f:
        f.write(header_bin)
        f.write(chunk1_header_bin)
        f.write(chunk1_data)
        f.write(chunk2_header_bin)
        f.write(chunk2_data)

    return str(sparse_file)

def test_unsparse(dummy_sparse_image, tmpdir):
    """Tests the unsparse functionality."""
    output_file = tmpdir.join("raw.img")

    sparse_image = SparseImage(dummy_sparse_image)
    sparse_image.unsparse(str(output_file))

    assert os.path.exists(output_file)

    with open(output_file, 'rb') as f:
        content = f.read()

    assert len(content) == 3 * 4096
    assert content[0:4096] == b'A' * 4096
    assert content[4096:4096*3] == struct.pack('<I', 0xBBBBBBBB) * (2 * 4096 // 4)
