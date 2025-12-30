import os

from textual.widgets import Tree
from textual.widgets.tree import TreeNode


class FileBrowser(Tree):
    """A file browser widget that loads directories on demand and supports filtering."""

    def __init__(self, path: str, **kwargs):
        super().__init__(label=os.path.basename(path), data=path, **kwargs)
        self.path = path
        self.filter_extensions: list[str] | None = None

    def set_filter(self, extensions: list[str] | None) -> None:
        """
        Sets a filter for file extensions.
        Args:
            extensions: A list of extensions to show (e.g., ['.ko', '.rc']).
                        Set to None to show all files.
        """
        self.filter_extensions = extensions
        # Clear the current tree and re-populate from the root to apply the filter
        self.root.remove_children()
        self._populate_directory(self.root)

    def _populate_directory(self, node: TreeNode) -> None:
        """Populates a node with the contents of its directory."""
        dir_path = node.data
        if not dir_path or not os.path.isdir(dir_path):
            return

        node.remove_children()

        try:
            paths = sorted(
                os.listdir(dir_path),
                key=lambda p: (not os.path.isdir(os.path.join(dir_path, p)), p.lower()),
            )
        except OSError:
            return

        for name in paths:
            path = os.path.join(dir_path, name)
            is_dir = os.path.isdir(path)

            if is_dir:
                child_node = node.add(name, data=path)
                child_node.add_leaf("Loading...")
            else:
                # If a filter is set, only show files with matching extensions
                if self.filter_extensions:
                    if any(name.endswith(ext) for ext in self.filter_extensions):
                        node.add_leaf(name, data=path)
                else:
                    # If no filter, show all files
                    node.add_leaf(name, data=path)

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        self._populate_directory(self.root)
        self.root.expand()

    def on_tree_node_expand(self, event: Tree.NodeExpanded) -> None:
        """Called when a user expands a node in the tree."""
        node = event.node
        if node.children and node.children[0].label == "Loading...":
            self._populate_directory(node)
