import subprocess
import shutil

class DtcHandler:
    """
    A wrapper for the dtc (Device Tree Compiler) tool.
    """

    def __init__(self):
        self._check_for_dtc()

    def _check_for_dtc(self):
        """
        Checks if dtc is installed and in the system's PATH.
        """
        if not shutil.which("dtc"):
            raise EnvironmentError(
                "dtc (Device Tree Compiler) is not installed or not in the "
                "system's PATH. Please install it to continue."
            )

    def decompile(self, dtb_path, dts_path):
        """
        Decompiles a Device Tree Blob (.dtb) to a Device Tree Source (.dts) file.
        """
        try:
            subprocess.run(
                ["dtc", "-I", "dtb", "-O", "dts", "-o", dts_path, dtb_path],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error decompiling DTB: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("dtc command not found.")

    def compile(self, dts_path, dtb_path):
        """
        Compiles a Device Tree Source (.dts) file to a Device Tree Blob (.dtb).
        """
        try:
            # The -@ flag is important for Android 15 overlays
            subprocess.run(
                ["dtc", "-@", "-I", "dts", "-O", "dtb", "-o", dtb_path, dts_path],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error compiling DTS: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("dtc command not found.")
