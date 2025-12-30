import argparse
import os
import sys

from android_15_tool.lib.scanner import MagicScanner
from android_15_tool.lib.unsparse import SparseImage
from android_15_tool.lib.super_unpacker import SuperUnpacker
from android_15_tool.lib.erofs_parser import ErofsParser
from android_15_tool.lib.boot_image import BootImage
from android_15_tool.lib.dtc_handler import DtcHandler
from android_15_tool.lib.repacker import Repacker
from android_15_tool.device_dumper import dump_partition

def handle_dump(args):
    """Handles the 'dump' command."""
    try:
        dump_partition(args.partition, args.output_dir)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def handle_search(args):
    """Handles the 'search' command."""
    scanner = MagicScanner()
    results = scanner.identify_image(args.file)
    print(f"Signatures found in {args.file}:")
    for res in results:
        print(f"- {res}")

def handle_extract(args):
    """Handles the 'extract' command."""
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    scanner = MagicScanner()
    image_types = scanner.identify_image(args.file)

    print(f"Identified image types: {', '.join(image_types)}")

    try:
        if 'Android Sparse' in image_types:
            print("Handling as a sparse image...")
            sparse_image = SparseImage(args.file)
            raw_image_path = os.path.join(args.output_dir, "raw_image.img")
            sparse_image.unsparse(raw_image_path)
            print(f"Unsparsed image saved to {raw_image_path}")

        elif 'Super Partition' in image_types or 'Super Partition (Offset 4096)' in image_types:
            print("Handling as a super partition...")
            super_unpacker = SuperUnpacker(args.file)
            super_unpacker.unpack(args.output_dir)
            print(f"Super partition unpacked to {args.output_dir}")

        elif 'EROFS Filesystem' in image_types:
            print("Handling as an EROFS filesystem...")
            erofs_parser = ErofsParser(args.file)
            erofs_parser.extract(args.output_dir)
            print(f"EROFS filesystem extracted to {args.output_dir}")

        elif 'Android Boot' in image_types:
            print("Handling as a boot/recovery image...")
            boot_image = BootImage(args.file)
            boot_image.unpack(args.output_dir)
            print(f"Boot image components extracted to {args.output_dir}")
        else:
            print("No supported image type found for extraction.")

    except (RuntimeError, EnvironmentError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def handle_repack(args):
    """Handles the 'repack' command."""
    try:
        repacker = Repacker(args.output)
        repacker.repack(args.header_info, args.kernel, args.ramdisk, args.dtb, args.cmdline, args.page_size)
        print(f"Image repacked to {args.output}")

        if args.avb_key:
            print("Signing with AVB...")
            repacker.sign_with_avb(args.avb_key)
            print("AVB signing complete (placeholder).")

    except (RuntimeError, EnvironmentError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def handle_dtc(args):
    """Handles the 'dtc' command."""
    try:
        handler = DtcHandler()
        if args.subcommand == "decompile":
            handler.decompile(args.dtb, args.dts)
            print(f"Decompiled {args.dtb} to {args.dts}")
        elif args.subcommand == "compile":
            handler.compile(args.dts, args.dtb)
            print(f"Compiled {args.dts} to {args.dtb}")

    except (RuntimeError, EnvironmentError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Android 15 Firmware and Recovery Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search command
    parser_search = subparsers.add_parser("search", help="Search for magic signatures in a file.")
    parser_search.add_argument("file", help="The file to search.")
    parser_search.set_defaults(func=handle_search)

    # Extract command
    parser_extract = subparsers.add_parser("extract", help="Extract a firmware or recovery image.")
    parser_extract.add_argument("file", help="The image file to extract.")
    parser_extract.add_argument("output_dir", help="The directory to extract the files to.")
    parser_extract.set_defaults(func=handle_extract)

    # Repack command
    parser_repack = subparsers.add_parser("repack", help="Repack a boot/recovery image.")
    parser_repack.add_argument("--header_info", required=True, help="Path to the header_info.txt file.")
    parser_repack.add_argument("--kernel", required=True, help="Path to the kernel file.")
    parser_repack.add_argument("--ramdisk", required=True, help="Path to the ramdisk file.")
    parser_repack.add_argument("--dtb", help="Path to the DTB file.")
    parser_repack.add_argument("--cmdline", default="", help="Command line arguments for the kernel.")
    parser_repack.add_argument("--output", default="image-new.img", help="Output file path.")
    parser_repack.add_argument("--page_size", type=int, default=4096, help="Page size for alignment.")
    parser_repack.add_argument("--avb_key", help="Path to the AVB signing key.")
    parser_repack.set_defaults(func=handle_repack)

    # DTC command
    parser_dtc = subparsers.add_parser("dtc", help="Decompile or recompile a Device Tree Blob.")
    dtc_subparsers = parser_dtc.add_subparsers(dest="subcommand", required=True)

    parser_decompile = dtc_subparsers.add_parser("decompile", help="Decompile a .dtb to a .dts file.")
    parser_decompile.add_argument("dtb", help="Path to the input .dtb file.")
    parser_decompile.add_argument("dts", help="Path to the output .dts file.")

    parser_compile = dtc_subparsers.add_parser("compile", help="Compile a .dts to a .dtb file.")
    parser_compile.add_argument("dts", help="Path to the input .dts file.")
    parser_compile.add_argument("dtb", help="Path to the output .dtb file.")
    parser_dtc.set_defaults(func=handle_dtc)

    # Dump command
    parser_dump = subparsers.add_parser("dump", help="Dump a partition from a rooted device.")
    parser_dump.add_argument("partition", help="The name of the partition to dump (e.g., boot, vendor_boot).")
    parser_dump.add_argument("output_dir", help="The directory to save the dumped image to.")
    parser_dump.set_defaults(func=handle_dump)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
