"""
Module for interacting with a rooted Android device to dump partitions.
"""
import subprocess
import logging
import os

logging.basicConfig(level=logging.INFO)

def run_adb_command(command):
    """Runs an ADB command and returns its output."""
    try:
        logging.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        if result.stderr:
            logging.warning(f"STDERR: {result.stderr.strip()}")
        return result.stdout.strip()
    except FileNotFoundError:
        logging.error("`adb` command not found. Is it installed and in your PATH?")
        raise
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {' '.join(e.cmd)}")
        logging.error(f"Exit Code: {e.returncode}")
        if e.stdout:
            logging.error(f"STDOUT: {e.stdout.strip()}")
        if e.stderr:
            logging.error(f"STDERR: {e.stderr.strip()}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise

def dump_partition(partition_name: str, output_dir: str):
    """
    Dumps a partition from the device to a local file.

    Args:
        partition_name: The name of the partition to dump (e.g., "boot").
        output_dir: The local directory to save the dumped image to.
    """
    device_tmp_path = f"/data/local/tmp/{partition_name}.img"
    local_path = os.path.join(output_dir, f"{partition_name}.img")

    os.makedirs(output_dir, exist_ok=True)

    logging.info(f"Starting dump for '{partition_name}' partition...")

    # 1. Dump partition to temporary location on device using dd
    dd_command = [
        "adb", "shell", "su", "-c",
        f"\"dd if=/dev/block/by-name/{partition_name} of={device_tmp_path}\""
    ]
    try:
        run_adb_command(dd_command)
        logging.info(f"Successfully dumped '{partition_name}' to '{device_tmp_path}' on device.")
    except subprocess.CalledProcessError:
        logging.error(f"Failed to dump partition '{partition_name}'. Does it exist? Do you have root?")
        return

    # 2. Pull the dumped image from device
    pull_command = ["adb", "pull", device_tmp_path, local_path]
    try:
        run_adb_command(pull_command)
        logging.info(f"Successfully pulled image to '{local_path}'.")
    except subprocess.CalledProcessError:
        logging.error(f"Failed to pull '{device_tmp_path}' from the device.")
        # Attempt to clean up even if pull fails
        run_adb_command(["adb", "shell", "su", "-c", f"\"rm {device_tmp_path}\""])
        return

    # 3. Clean up the temporary file on device
    rm_command = ["adb", "shell", "su", "-c", f"\"rm {device_tmp_path}\""]
    try:
        run_adb_command(rm_command)
        logging.info(f"Successfully cleaned up temporary file on device.")
    except subprocess.CalledProcessError:
        logging.warning(f"Failed to clean up '{device_tmp_path}' on the device. Manual cleanup may be required.")

    logging.info(f"Partition dump complete for '{partition_name}'.")
