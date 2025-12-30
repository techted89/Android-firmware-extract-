import os
import pytest
from textual.pilot import Pilot

from android_15_tool.lib.tui.app import TuiApp
from android_15_tool.lib.tui.widgets.file_browser import FileBrowser

KO_FILE = "test.ko"
RC_FILE = "init.test.rc"
OTHER_FILE = "README.md"


@pytest.fixture
def app() -> TuiApp:
    """Return a TuiApp instance in the context of a temporary directory."""
    # Create a temporary directory for the test
    os.makedirs("test_dir", exist_ok=True)
    os.chdir("test_dir")

    with open(KO_FILE, "w") as f:
        f.write("dummy ko file")
    with open(RC_FILE, "w") as f:
        f.write("dummy rc file")
    with open(OTHER_FILE, "w") as f:
        f.write("dummy readme file")

    app = TuiApp()
    yield app

    os.remove(KO_FILE)
    os.remove(RC_FILE)
    os.remove(OTHER_FILE)
    os.chdir("..")
    os.rmdir("test_dir")


async def test_tui_app_startup(app: TuiApp):
    """Test that the TUI app can be instantiated without errors."""
    async with app.run_test() as pilot:
        assert isinstance(pilot, Pilot)
        assert app.is_running


async def test_file_browser_filtering(app: TuiApp):
    """Test that the file browser's visible nodes change with filtering."""
    async with app.run_test() as pilot:
        file_browser = pilot.app.query_one(FileBrowser)

        # Helper to get visible leaf labels
        def get_visible_leaves(tree):
            labels = []
            try:
                for node in tree.children:
                    if not node.allow_expand:
                        labels.append(str(node.label))
            except Exception:
                # Ignore errors if the tree is not yet populated
                pass
            return labels

        # Initially, all files should be visible
        initial_leaves = get_visible_leaves(file_browser.root)
        assert KO_FILE in initial_leaves
        assert RC_FILE in initial_leaves
        assert OTHER_FILE in initial_leaves

        # Click the .ko radio button and check visibility
        await pilot.click("#ko")
        await pilot.pause() # Allow UI to update
        ko_leaves = get_visible_leaves(file_browser.root)
        assert KO_FILE in ko_leaves
        assert RC_FILE not in ko_leaves
        assert OTHER_FILE not in ko_leaves

        # Click the .rc radio button
        await pilot.click("#rc")
        await pilot.pause()
        rc_leaves = get_visible_leaves(file_browser.root)
        assert KO_FILE not in rc_leaves
        assert RC_FILE in rc_leaves
        assert OTHER_FILE not in rc_leaves

        # Click the all radio button
        await pilot.click("#all")
        await pilot.pause()
        all_leaves = get_visible_leaves(file_browser.root)
        assert KO_FILE in all_leaves
        assert RC_FILE in all_leaves
        assert OTHER_FILE in all_leaves
