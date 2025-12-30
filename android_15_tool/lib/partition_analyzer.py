from android_15_tool.lib.super_unpacker import SuperUnpacker

def analyze_partition_image(image_path: str) -> dict:
    """
    Analyzes a partition image file (e.g., super.img) and returns a dictionary
    of partition information.
    """
    try:
        unpacker = SuperUnpacker(image_path)
        with open(image_path, 'rb') as f:
            unpacker._parse_metadata(f)

        if unpacker.metadata and unpacker.metadata["partitions"]:
            # For now, we are not calculating the size.
            # This can be added later by parsing the extents.
            partitions = [
                {"name": p["name"], "size": "N/A"}
                for p in unpacker.metadata["partitions"]
            ]
            return {
                "status": "success",
                "partitions": partitions,
            }
        else:
            return {
                "status": "success",
                "partitions": [],
                "note": "No partitions found. This may not be a valid super.img file.",
            }

    except (RuntimeError, ValueError) as e:
        return {"status": "error", "message": str(e)}
