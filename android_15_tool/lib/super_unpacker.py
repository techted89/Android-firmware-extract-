import os
import struct


class SuperUnpacker:
    """
    Parses super.img partitions by first reading the LpMetadataGeometry
    and then finding the active LpMetadataHeader.
    """

    SPARSE_HEADER_MAGIC = 0x3AFF26ED
    LP_METADATA_GEOMETRY_MAGIC = 0x614c5047
    LP_METADATA_HEADER_MAGIC = 0x414C5030
    LP_PARTITION_RESERVED_BYTES = 4096

    LP_METADATA_GEOMETRY_FORMAT = '<II32sIII'
    LP_METADATA_GEOMETRY_SIZE = struct.calcsize(LP_METADATA_GEOMETRY_FORMAT)

    LP_METADATA_TABLE_DESCRIPTOR_FORMAT = '<III'
    LP_METADATA_TABLE_DESCRIPTOR_SIZE = struct.calcsize(LP_METADATA_TABLE_DESCRIPTOR_FORMAT)

    # V1.0 of the header. Later versions add fields at the end.
    LP_METADATA_HEADER_V1_0_FORMAT = '<IHH I 32s I 32s'
    LP_METADATA_HEADER_V1_0_SIZE = struct.calcsize(LP_METADATA_HEADER_V1_0_FORMAT)

    def __init__(self, filepath):
        self.filepath = filepath
        self.geometry = None
        self.metadata = None
        self.logical_block_size = None

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
        f.seek(self.LP_PARTITION_RESERVED_BYTES)
        geo_data = f.read(self.LP_METADATA_GEOMETRY_SIZE)
        if len(geo_data) < self.LP_METADATA_GEOMETRY_SIZE:
            raise ValueError("File too small to contain Geometry")

        geo = struct.unpack(self.LP_METADATA_GEOMETRY_FORMAT, geo_data)

        if geo[0] != self.LP_METADATA_GEOMETRY_MAGIC:
            # Check for 16KB alignment (Android 15)
            f.seek(16384)
            geo_data = f.read(self.LP_METADATA_GEOMETRY_SIZE)
            if len(geo_data) < self.LP_METADATA_GEOMETRY_SIZE:
                raise ValueError("File too small to contain Geometry")
            geo = struct.unpack(self.LP_METADATA_GEOMETRY_FORMAT, geo_data)
            if geo[0] != self.LP_METADATA_GEOMETRY_MAGIC:
                raise ValueError("Invalid Geometry Magic. Is this a Sparse image?")

        self.geometry = {
            "struct_size": geo[1],
            "checksum": geo[2],
            "metadata_max_size": geo[3],
            "metadata_slot_count": geo[4],
            "logical_block_size": geo[5],
        }
        self.logical_block_size = self.geometry["logical_block_size"]

        # 2. Find and parse the active LpMetadataHeader
        for i in range(self.geometry["metadata_slot_count"]):
            slot_offset = self.LP_PARTITION_RESERVED_BYTES + self.LP_METADATA_GEOMETRY_SIZE + (i * self.geometry["metadata_max_size"])
            f.seek(slot_offset)

            # Read enough to get header size, magic, etc.
            header_prefix_size = struct.calcsize('<IHH I')
            header_prefix = f.read(header_prefix_size)
            if len(header_prefix) < header_prefix_size:
                continue

            magic, _, _, header_size = struct.unpack('<IHH I', header_prefix)

            if magic != self.LP_METADATA_HEADER_MAGIC:
                continue

            f.seek(slot_offset)
            header_data = f.read(header_size)
            if len(header_data) < header_size:
                raise ValueError("Could not read full metadata header.")

            header_main = struct.unpack(self.LP_METADATA_HEADER_V1_0_FORMAT,
                                        header_data[:self.LP_METADATA_HEADER_V1_0_SIZE])

            self.metadata = {
                "major_version": header_main[1],
                "minor_version": header_main[2],
                "header_size": header_main[3],
                "tables_size": header_main[5],
                "partitions": [],
                "extents": [],
            }

            # Unpack descriptors which follow the main header struct
            desc_offset = self.LP_METADATA_HEADER_V1_0_SIZE

            partitions_desc_raw = header_data[desc_offset : desc_offset + self.LP_METADATA_TABLE_DESCRIPTOR_SIZE]
            desc_offset += self.LP_METADATA_TABLE_DESCRIPTOR_SIZE

            extents_desc_raw = header_data[desc_offset : desc_offset + self.LP_METADATA_TABLE_DESCRIPTOR_SIZE]
            desc_offset += self.LP_METADATA_TABLE_DESCRIPTOR_SIZE

            groups_desc_raw = header_data[desc_offset : desc_offset + self.LP_METADATA_TABLE_DESCRIPTOR_SIZE]
            desc_offset += self.LP_METADATA_TABLE_DESCRIPTOR_SIZE

            block_devices_desc_raw = header_data[desc_offset : desc_offset + self.LP_METADATA_TABLE_DESCRIPTOR_SIZE]

            partitions_desc = struct.unpack(self.LP_METADATA_TABLE_DESCRIPTOR_FORMAT, partitions_desc_raw)
            extents_desc = struct.unpack(self.LP_METADATA_TABLE_DESCRIPTOR_FORMAT, extents_desc_raw)
            groups_desc = struct.unpack(self.LP_METADATA_TABLE_DESCRIPTOR_FORMAT, groups_desc_raw)
            block_devices_desc = struct.unpack(self.LP_METADATA_TABLE_DESCRIPTOR_FORMAT, block_devices_desc_raw)

            self.metadata['partitions_table'] = {
                "offset": partitions_desc[0],
                "num_entries": partitions_desc[1],
                "entry_size": partitions_desc[2],
            }
            self.metadata['extents_table'] = {
                "offset": extents_desc[0],
                "num_entries": extents_desc[1],
                "entry_size": extents_desc[2],
            }
            self.metadata['groups_table'] = {
                "offset": groups_desc[0],
                "num_entries": groups_desc[1],
                "entry_size": groups_desc[2],
            }
            self.metadata['block_devices_table'] = {
                "offset": block_devices_desc[0],
                "num_entries": block_devices_desc[1],
                "entry_size": block_devices_desc[2],
            }

            self._parse_partitions(f, slot_offset)
            self._parse_extents(f, slot_offset)
            self._parse_block_devices(f, slot_offset)
            return

        raise ValueError("No active LpMetadataHeader found in any slot.")

    def parse(self):
        """Parses the super.img file."""
        with open(self.filepath, 'rb') as f:
            self._parse_metadata(f)

    def _parse_partitions(self, f, slot_offset):
        """Reads and parses the partition table."""
        table_offset = slot_offset + self.metadata['header_size'] + self.metadata['partitions_table']['offset']
        f.seek(table_offset)

        entry_format = '<36sIIII'
        entry_size = self.metadata['partitions_table']['entry_size']

        for _ in range(self.metadata['partitions_table']['num_entries']):
            part_bin = f.read(entry_size)
            if len(part_bin) < entry_size:
                raise ValueError("Could not read full partition entry.")

            name_bin, attrs, first_extent, num_extents, group_idx = struct.unpack(entry_format, part_bin)
            name = name_bin.decode('utf-8').rstrip('\x00')

            if name:
                self.metadata["partitions"].append({
                    "name": name,
                    "attributes": attrs,
                    "first_extent_index": first_extent,
                    "num_extents": num_extents,
                    "group_index": group_idx,
                })

    def _parse_extents(self, f, slot_offset):
        """Reads and parses the extent table."""
        table_offset = slot_offset + self.metadata['header_size'] + self.metadata['extents_table']['offset']
        f.seek(table_offset)

        entry_format = '<QIQI'
        entry_size = self.metadata['extents_table']['entry_size']

        for _ in range(self.metadata['extents_table']['num_entries']):
            extent_bin = f.read(entry_size)
            if len(extent_bin) < entry_size:
                raise ValueError("Could not read full extent entry.")

            num_sectors, target_type, target_data, target_source = struct.unpack(entry_format, extent_bin)

            self.metadata["extents"].append({
                "num_sectors": num_sectors,
                "target_type": target_type,
                "target_data": target_data,
                "target_source": target_source,
            })

    def _parse_block_devices(self, f, slot_offset):
        """Reads and parses the block_devices table."""
        table_offset = slot_offset + self.metadata['header_size'] + self.metadata['block_devices_table']['offset']
        f.seek(table_offset)

        entry_format = '<QIIQ36sI'
        entry_size = self.metadata['block_devices_table']['entry_size']
        if struct.calcsize(entry_format) != entry_size:
             raise ValueError(f"Block device entry size mismatch. Expected {struct.calcsize(entry_format)}, got {entry_size}")

        self.metadata["block_devices"] = []
        for _ in range(self.metadata['block_devices_table']['num_entries']):
            device_bin = f.read(entry_size)
            if len(device_bin) < entry_size:
                raise ValueError("Could not read full block_device entry.")

            first_sector, align, align_off, size, name_bin, flags = struct.unpack(entry_format, device_bin)
            name = name_bin.decode('utf-8').rstrip('\x00')

            self.metadata["block_devices"].append({
                "first_logical_sector": first_sector,
                "alignment": align,
                "alignment_offset": align_off,
                "size": size,
                "partition_name": name,
                "flags": flags,
            })

    def unpack(self, output_dir, partitions_to_extract=None):
        """
        Extracts the logical partitions to the output directory.
        If partitions_to_extract is provided, only those partitions will be extracted.
        """
        try:
            with open(self.filepath, 'rb') as f:
                self.parse()

                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                if not self.metadata.get("block_devices"):
                     raise RuntimeError("No block devices found in metadata.")

                # Create a map of block device names to their file objects
                block_device_files = {}
                for i, device in enumerate(self.metadata["block_devices"]):
                    if i == 0:  # The first block device is the super.img itself
                        block_device_files[i] = f
                    else:
                        # For other block devices, we assume they are in the same directory as the super.img
                        device_path = os.path.join(os.path.dirname(self.filepath), device["partition_name"])
                        if os.path.exists(device_path):
                            block_device_files[i] = open(device_path, 'rb')
                        else:
                            print(f"Warning: Block device {device['partition_name']} not found. Skipping extents on this device.")

                for partition in self.metadata["partitions"]:
                    partition_name = partition["name"]
                    if partitions_to_extract and partition_name not in partitions_to_extract:
                        continue

                    output_path = os.path.join(output_dir, f"{partition_name}.img")

                    with open(output_path, 'wb') as out_f:
                        first_extent_idx = partition["first_extent_index"]
                        num_extents = partition["num_extents"]

                        for i in range(num_extents):
                            extent = self.metadata["extents"][first_extent_idx + i]

                            LP_TARGET_TYPE_LINEAR = 0
                            LP_TARGET_TYPE_ZERO = 1

                            if extent["target_type"] == LP_TARGET_TYPE_ZERO:
                                length = extent["num_sectors"] * self.logical_block_size
                                out_f.write(b'\0' * length)

                            elif extent["target_type"] == LP_TARGET_TYPE_LINEAR:
                                target_source = extent["target_source"]
                                if target_source not in block_device_files:
                                    print(f"Warning: Skipping extent on missing block device {target_source}")
                                    continue

                                source_f = block_device_files[target_source]
                                block_device = self.metadata["block_devices"][target_source]
                                read_offset = (block_device["first_logical_sector"] * self.logical_block_size) + (extent["target_data"] * self.logical_block_size)
                                length = extent["num_sectors"] * self.logical_block_size

                                source_f.seek(read_offset)
                                remaining_bytes = length
                                chunk_size = 1024 * 1024  # 1MB chunks
                                while remaining_bytes > 0:
                                    read_size = min(chunk_size, remaining_bytes)
                                    chunk = source_f.read(read_size)
                                    if not chunk:
                                        raise IOError(f"Unexpected end of file for {partition_name}")
                                    out_f.write(chunk)
                                    remaining_bytes -= len(chunk)
                            else:
                                print(f"Warning: Unsupported extent target type {extent['target_type']} for partition {partition_name}")

                # Close any opened block device files
                for i, file in block_device_files.items():
                    if i != 0:
                        file.close()

        except (ValueError, struct.error, IOError) as e:
            raise RuntimeError(f"Error processing super.img: {e}")
