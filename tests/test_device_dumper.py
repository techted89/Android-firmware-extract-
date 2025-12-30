"""
Tests for the device_dumper module.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import subprocess
from android_15_tool.device_dumper import dump_partition

class TestDeviceDumper(unittest.TestCase):

    @patch('subprocess.run')
    def test_dump_partition_success(self, mock_run):
        """Test successful partition dumping."""
        # Arrange
        mock_run.return_value = MagicMock(
            capture_output=True, text=True, check=True,
            stdout="Success", stderr=""
        )
        partition_name = "boot"
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)

        # Act
        dump_partition(partition_name, output_dir)

        # Assert
        self.assertEqual(mock_run.call_count, 3)

        # Check dd command
        dd_call_args = mock_run.call_args_list[0].args[0]
        self.assertIn("dd if=/dev/block/by-name/boot of=/data/local/tmp/boot.img", dd_call_args[-1])

        # Check pull command
        pull_call_args = mock_run.call_args_list[1].args[0]
        self.assertEqual(pull_call_args, ["adb", "pull", "/data/local/tmp/boot.img", os.path.join(output_dir, "boot.img")])

        # Check rm command
        rm_call_args = mock_run.call_args_list[2].args[0]
        self.assertIn("rm /data/local/tmp/boot.img", rm_call_args[-1])

        # Cleanup - Create a dummy file to be removed
        local_path = os.path.join(output_dir, "boot.img")
        with open(local_path, "w") as f:
            f.write("dummy")

        os.remove(local_path)
        os.rmdir(output_dir)

    @patch('subprocess.run')
    def test_dump_partition_dd_fails(self, mock_run):
        """Test failure when dd command fails."""
        # Arrange
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "cmd", stderr="Permission denied"),
            MagicMock(), # for cleanup call
            MagicMock()
        ]
        partition_name = "system"
        output_dir = "test_output"

        # Act
        dump_partition(partition_name, output_dir)

        # Assert
        self.assertEqual(mock_run.call_count, 1) # Should only try dd
        local_path = os.path.join(output_dir, "system.img")
        self.assertFalse(os.path.exists(local_path)) # File should not be created

if __name__ == '__main__':
    unittest.main()
