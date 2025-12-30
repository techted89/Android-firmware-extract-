import os

from textual.app import App
from textual.widgets import Header, Footer, Log, RadioSet, RadioButton, Label, Tree
from textual.containers import VerticalScroll

from android_15_tool.lib.driver_finder import find_touchscreen_drivers
from android_15_tool.lib.partition_analyzer import analyze_partition_image
from android_15_tool.lib.recovery_scanner import find_recovery_images
from android_15_tool.lib.tui.widgets.file_browser import FileBrowser


class TuiApp(App):
    """The main application for the TUI."""

    def compose(self):
        """Compose the layout of the application."""
        yield Header()
        with VerticalScroll():
            yield FileBrowser("./", id="file_browser")
            yield Label("Filter files:")
            yield RadioSet(
                RadioButton("All", id="all", value=True),
                RadioButton("Kernel Modules (*.ko)", id="ko"),
                RadioButton("Init Scripts (*.rc)", id="rc"),
                id="filter_radio_set",
            )
        yield Log(id="log")
        yield Footer()

    def on_mount(self):
        """Called when the app is mounted."""
        log = self.query_one(Log)
        log.write("Android 15 TWRP Helper TUI Initialized.")
        log.write("Select a directory or file in the browser to analyze.")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Called when a node is selected in the file browser."""
        log = self.query_one(Log)
        path = event.node.data
        if not (path and event.node.is_cursor_on):
            return

        log.clear()
        if os.path.isdir(path):
            log.write(f"Scanning directory: {path}")
            try:
                recovery_images = find_recovery_images(str(path))
                drivers = find_touchscreen_drivers(str(path))

                log.write("\n--- Directory Scan Results ---")
                if recovery_images:
                    log.write("Recovery Images Found:")
                    for image in recovery_images:
                        log.write(f"- {image}")
                else:
                    log.write("No potential recovery images found.")

                if drivers:
                    log.write("\nTouchscreen Drivers Found:")
                    for driver in drivers:
                        log.write(f"- {driver}")
                else:
                    log.write("No potential touchscreen drivers found.")
                log.write("--- End of Scan ---")
            except Exception as e:
                log.write(f"[ERROR] Failed to scan directory: {e}")
        elif os.path.isfile(path):
            log.write(f"Analyzing file: {path}")
            results = analyze_partition_image(str(path))

            log.write("\n--- Partition Analysis Results ---")
            if results["status"] == "success":
                if results.get("note"):
                    log.write(f"NOTE: {results['note']}")

                if results["partitions"]:
                    log.write("Partitions Found:")
                    for part in results["partitions"]:
                        log.write(f"- Name: {part['name']}, Size: {part['size']}")
                else:
                    log.write("No partition information found (this may not be a super.img).")
            else:
                log.write(f"[ERROR] {results['message']}")
            log.write("--- End of Analysis ---")


    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Called when the radio button selection changes."""
        file_browser = self.query_one(FileBrowser)
        if event.pressed.id == "all":
            file_browser.set_filter(None)
        elif event.pressed.id == "ko":
            file_browser.set_filter([".ko"])
        elif event.pressed.id == "rc":
            file_browser.set_filter([".rc"])
