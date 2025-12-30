import os

def find_recovery_images(search_path="."):
    """Finds recovery images in the specified path."""
    recovery_image_names = [
        "recovery.img",
        "boot.img",
        "vendor_boot.img",
        "init_boot.img",
    ]
    found_images = []
    for root, _, files in os.walk(search_path):
        for file in files:
            if file in recovery_image_names:
                found_images.append(os.path.join(root, file))
    return found_images
