import struct

class SuperUnpacker:
    """
    Parses super.img partitions by first reading the LpMetadataGeometry
    and then finding the active LpMetadataHeader.
    """

    SPARSE_HEADER_MAGIC = 0x3AFF26ED
    LP_METADATA_GEOMETRY_MAGIC = 0x616c7067
    LP_METADATA_HEADER_MAGIC = 0x414C5030
    LP_METADATA_GEOMETRY_SIZE = 52
    LP_METADATA_HEADER_MIN_SIZE = 104

    def __init__(self, filepath):
        self.filepath = filepath
        self.geometry = None
        self.metadata = None

    def _parse_metadata(self, f):
        """
        Parses the LpMetadata from the super.img.
        """
        # 0. Check for sparse image format
        f.seek(0)
        magic = struct.unpack('<I', f.read(4))[0]
        if magic == self.SPARSE_HEADER_MAGIC:
            raise ValueError("Sparse images are not supported. Please unsparse the image first.")

        # 1. Find and parse the LpMetadataGeometry
        f.seek(4096)
        geo_data = f.read(self.LP_METADATA_GEOMETRY_SIZE)
        if len(geo_data) < self.LP_METADATA_GEOMETRY_SIZE:
            raise ValueError("File too small to contain Geometry")

        geo = struct.unpack('<II32sIII', geo_data)

        if geo[0] != self.LP_METADATA_GEOMETRY_MAGIC:
            # Check for 16KB alignment (Android 15)
            f.seek(16384)
            geo_data = f.read(self.LP_METADATA_GEOMETRY_SIZE)
            geo = struct.unpack('<II32sIII', geo_data)
            if geo[0] != self.LP_METADATA_GEOMETRY_MAGIC:
                raise ValueError("Invalid Geometry Magic. Is this a Sparse image?")

        self.geometry = {
            "metadata_max_size": geo[3],
            "metadata_slot_count": geo[4],
        }

        # 2. Find and parse the active LpMetadataHeader
        for i in range(self.geometry["metadata_slot_count"]):
            slot_offset = 8192 + (i * self.geometry["metadata_max_size"])
            f.seek(slot_offset)
            header_data = f.read(self.LP_METADATA_HEADER_MIN_SIZE)

            header_format = '<IHH I 32s I 32s I 20x'
            if len(header_data) < struct.calcsize(header_format):
                raise ValueError("Header data too small to unpack")

            header = struct.unpack(header_format, header_data)

            if header[0] != self.LP_METADATA_HEADER_MAGIC:
                continue

            self.metadata = {"partitions": []}
            header_size = header[3]
            partitions_size = header[5]

            # The partition table is immediately after the header.
            partitions_offset = header_size

            partition_entry_size = 52 # sizeof(LpMetadataPartition)
            partition_table_count = partitions_size // partition_entry_size

            f.seek(slot_offset + partitions_offset)
            for _ in range(partition_table_count):
                part_bin = f.read(partition_entry_size)
                # We only need the name, so we don't unpack the whole struct.
                name_bin = struct.unpack('<36s', part_bin[:36])[0]
                name = name_bin.decode('utf-8').rstrip('\x00')
                if name:
                    self.metadata["partitions"].append({"name": name})
            return

        raise ValueError("No active LpMetadataHeader found in any slot.")

    def unpack(self, output_dir):
        """
        Extracts the logical partitions to the output directory.
        """
        try:
            with open(self.filepath, 'rb') as f:
                self._parse_metadata(f)
        except (ValueError, struct.error) as e:
            raise RuntimeError(f"Error processing super.img: {e}")
