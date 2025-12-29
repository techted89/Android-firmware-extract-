import struct

class MagicScanner:
    """
    Identifies firmware and recovery image types based on magic bytes and offsets.
    """

    MAGIC_SIGNATURES = {
        'Android Sparse':      {'magic': b'\x3A\xFF\x26\xED', 'offset': 0},
        'Super Partition':     {'magic': b'\x4C\x6B\x44\x61', 'offset': 0},
        'EROFS Filesystem':    {'magic': b'\xE2\xE1\xF5\xE0', 'offset': 1024},
        'OTA Payload':         {'magic': b'PAYLOAD',        'offset': 0},
        'Android Boot':        {'magic': b'ANDROID!',       'offset': 0},
        'DTB':                 {'magic': b'\xd0\x0d\xfe\xed', 'offset': -1},
        'AVB 2.0 Footer':      {'magic': b'AVBb',           'offset': -1},
        'LZ4 Ramdisk':         {'magic': b'\x04\x22\x4d\x18', 'offset': -1},
        'DTC Table':           {'magic': b'TDBL',           'offset': -1},
    }

    def search_for_magic(self, f, magic):
        """
        Searches for a magic byte sequence within a file.
        """
        f.seek(0)
        content = f.read()
        return magic in content

    def identify_image(self, filepath):
        """
        Identifies the type of the image file.
        Returns a list of all identified signatures.
        """
        results = []
        try:
            with open(filepath, 'rb') as f:
                # Check fixed offsets first
                for name, sig in self.MAGIC_SIGNATURES.items():
                    if sig['offset'] >= 0:
                        f.seek(sig['offset'])
                        if f.read(len(sig['magic'])) == sig['magic']:
                            results.append(name)

                # Handle special case for Super Partition at offset 4096
                f.seek(4096)
                if f.read(len(self.MAGIC_SIGNATURES['Super Partition']['magic'])) == self.MAGIC_SIGNATURES['Super Partition']['magic']:
                    if 'Super Partition' not in results:
                        results.append('Super Partition (Offset 4096)')

                # Search for variable offset signatures
                # For AVB, check the last 64KB
                f.seek(0, 2)
                file_size = f.tell()
                f.seek(max(0, file_size - 65536))
                if self.MAGIC_SIGNATURES['AVB 2.0 Footer']['magic'] in f.read():
                     results.append('AVB 2.0 Footer')

                # Search the whole file for the rest
                if self.search_for_magic(f, self.MAGIC_SIGNATURES['DTB']['magic']):
                    results.append('DTB')
                if self.search_for_magic(f, self.MAGIC_SIGNATURES['LZ4 Ramdisk']['magic']):
                    results.append('LZ4 Ramdisk')
                if self.search_for_magic(f, self.MAGIC_SIGNATURES['DTC Table']['magic']):
                    results.append('DTC Table')

        except FileNotFoundError:
            return ["File not found"]
        except IOError:
            return ["Error reading file"]

        if not results:
            return ["Unknown"]

        return results
