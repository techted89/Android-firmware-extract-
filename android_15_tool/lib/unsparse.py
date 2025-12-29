import struct
import os

class SparseImage:
    """
    Handles the conversion of Android sparse images to raw images.
    """

    SPARSE_HEADER_MAGIC = 0xed26ff3a
    CHUNK_TYPE_RAW = 0xCAC1
    CHUNK_TYPE_FILL = 0xCAC2
    CHUNK_TYPE_DONT_CARE = 0xCAC3
    CHUNK_TYPE_CRC32 = 0xCAC4

    def __init__(self, filepath):
        self.filepath = filepath
        self.header = None
        self.chunks = []

    def _parse_header(self, f):
        """
        Parses the sparse image header.
        """
        header_bin = f.read(28)
        if len(header_bin) < 28:
            raise ValueError("Invalid sparse image: header too short.")

        header_data = struct.unpack('<I4H4I', header_bin)
        self.header = {
            'magic': header_data[0],
            'major_version': header_data[1],
            'minor_version': header_data[2],
            'file_hdr_sz': header_data[3],
            'chunk_hdr_sz': header_data[4],
            'blk_sz': header_data[5],
            'total_blks': header_data[6],
            'total_chunks': header_data[7],
            'image_checksum': header_data[8],
        }

        if self.header['magic'] != self.SPARSE_HEADER_MAGIC:
            raise ValueError("Invalid sparse image: incorrect magic.")

    def _parse_chunks(self, f):
        """
        Parses the chunks of the sparse image.
        """
        for _ in range(self.header['total_chunks']):
            chunk_header_bin = f.read(12)
            if len(chunk_header_bin) < 12:
                raise ValueError("Invalid sparse image: chunk header too short.")

            chunk_header_data = struct.unpack('<2H2I', chunk_header_bin)
            chunk = {
                'type': chunk_header_data[0],
                'reserved1': chunk_header_data[1],
                'chunk_sz': chunk_header_data[2],
                'total_sz': chunk_header_data[3],
            }

            data_sz = chunk['total_sz'] - self.header['chunk_hdr_sz']
            chunk['data'] = f.read(data_sz)
            self.chunks.append(chunk)

    def unsparse(self, output_filepath):
        """
        Converts the sparse image to a raw image.
        """
        try:
            with open(self.filepath, 'rb') as f_in:
                self._parse_header(f_in)
                self._parse_chunks(f_in)

            with open(output_filepath, 'wb') as f_out:
                for chunk in self.chunks:
                    chunk_sz_bytes = chunk['chunk_sz'] * self.header['blk_sz']
                    if chunk['type'] == self.CHUNK_TYPE_RAW:
                        f_out.write(chunk['data'])
                    elif chunk['type'] == self.CHUNK_TYPE_FILL:
                        fill_val = struct.unpack('<I', chunk['data'])[0]
                        fill_data = struct.pack('<I', fill_val) * (chunk_sz_bytes // 4)
                        f_out.write(fill_data)
                    elif chunk['type'] == self.CHUNK_TYPE_DONT_CARE:
                        f_out.seek(chunk_sz_bytes, os.SEEK_CUR)
                    elif chunk['type'] == self.CHUNK_TYPE_CRC32:
                        # For now, we are not validating the checksum
                        pass

        except (ValueError, struct.error) as e:
            raise RuntimeError(f"Error processing sparse image: {e}")
        except FileNotFoundError:
            raise RuntimeError(f"Input file not found: {self.filepath}")
        except IOError as e:
            raise RuntimeError(f"I/O error: {e}")
