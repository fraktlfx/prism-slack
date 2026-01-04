import os
import webbrowser
from typing import Any

from client.prism.api import API
from qtpy.QtWidgets import QAction, QMenu


def projectBrowser_loadUI(core: Any, origin: Any):
    """
    Load the Slack UI in the project browser window.

    Args:
        core (Any): The core application object.
        origin (Any): The ProjectBrowser window instance.
    """
    ui = ProjectBrowserUI(core)
    ui.create_project_browser_ui(origin)


class ProjectBrowserUI:
    def __init__(self, core):
        self.core = core

    # Create the Project Browser UI for the Slack Server
    def create_project_browser_ui(self, origin):
        """
        Add Slack menu to the Project Browser menu bar.

        Args:
            origin: The ProjectBrowser window instance.
        """
        # Create Slack menu
        slack_menu = QMenu("Slack", origin)

        # Add menu actions
        self.website = QAction("Website", origin)
        self.website_icon = self.core.media.getColoredIcon(
            os.path.join(self.core.prismRoot, "Scripts", "UserInterfacesPrism", "open-web.png")
        )
        self.website.setIcon(self.website_icon)
        self.website.triggered.connect(
            lambda: webbrowser.open("https://fraktlfx.com/pipeline/prism-slack")
        )

        self.documentation = QAction("Documentation", origin)
        self.documentation_icon = self.core.media.getColoredIcon(
            os.path.join(self.core.prismRoot, "Scripts", "UserInterfacesPrism", "book.png")
        )
        self.documentation.setIcon(self.documentation_icon)
        self.documentation.triggered.connect(
            lambda: webbrowser.open("https://docs.fraktlfx.com/prism/slack")
        )

        self.manage_license = QAction("Manage License(s)", origin)
        self.manage_license_icon = self.core.media.getColoredIcon(
            os.path.join(self.core.prismRoot, "Scripts", "UserInterfacesPrism", "user.png")
        )

        slack_menu.addAction(self.website)
        slack_menu.addAction(self.documentation)

        # Add to the menu bar
        if hasattr(origin, "menubar"):
            origin.menubar.addMenu(slack_menu)
