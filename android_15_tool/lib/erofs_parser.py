import subprocess
import shutil

class ErofsParser:
    """
    A wrapper for erofs-utils to list and extract files from EROFS images.
    """

    def __init__(self, filepath):
        self.filepath = filepath
        self._check_for_erofs_utils()

    def _check_for_erofs_utils(self):
        """
        Checks if the erofs-utils (specifically dump.erofs) are installed.
        """
        if not shutil.which("dump.erofs"):
            raise EnvironmentError(
                "erofs-utils is not installed or not in the system's PATH. "
                "Please install it to continue."
            )

    def list_files(self):
        """
        Lists the files in the EROFS image.
        Returns a list of file paths.
        """
        try:
            result = subprocess.run(
                ["dump.erofs", "-l", self.filepath],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n')
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error listing EROFS files: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("dump.erofs command not found.")

    def extract(self, output_dir):
        """
        Extracts the EROFS image to the specified output directory.
        """
        try:
            subprocess.run(
                ["dump.erofs", "-x", "-o", output_dir, self.filepath],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error extracting EROFS image: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("dump.erofs command not found.")
