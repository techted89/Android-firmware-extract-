import os
import re

def find_touchscreen_drivers(search_path="."):
    """Finds touchscreen drivers in the specified path."""
    driver_files = set()

    # Find .ko files
    for root, _, files in os.walk(search_path):
        for file in files:
            if file.endswith(".ko"):
                driver_files.add(os.path.join(root, file))

    # Find insmod commands in init.rc files
    for root, _, files in os.walk(search_path):
        for file in files:
            if file.startswith("init") and file.endswith(".rc"):
                try:
                    with open(os.path.join(root, file), "r") as f:
                        for line in f:
                            match = re.search(r"insmod\s+([/\w\.-]+ko)", line)
                            if match:
                                driver_files.add(match.group(1))
                except (IOError, UnicodeDecodeError):
                    # Ignore files that can't be read
                    continue

    return sorted(list(driver_files))
