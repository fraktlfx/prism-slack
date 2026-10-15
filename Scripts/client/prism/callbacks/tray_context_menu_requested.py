import os
import socket
from pathlib import Path

from prism_slack.client.prism.ui import ServerNonWarning
from prism_slack.client.prism.ui.tray_ui import TrayUI
from prism_slack.client.slack.slack_config import SlackConfig
from prism_slack.server.controls import ServerControls

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QWidget, QMenu


class TrayContextMenuRequested:
    """
    Add Slack server controls to the system tray context menu.

    Args:
        core (object): The core application object.
        origin (QWidget): The origin object requesting the context menu.
        menu (QMenu): The context menu object to which Slack options will be added.
    """

    def __init__(self, core: object):
        self.core = core
        self.tray_ui: TrayUI | None = None
        self.plugin_directory = Path(__file__).resolve().parents[4]

    def __call__(self, origin: QWidget, menu: QMenu):
        config = SlackConfig(self.core).load_config(mode="studio")
        SlackConfig(self.core).check_slack_studio_options(config)

        server_status = config["slack"]["server"].get("status")
        server_machine = config["slack"]["server"].get("machine")

        # Set the server status in the tray to "Not running" if it is empty
        if server_status == "":
            server_status = "Not running"

        if server_machine == "":
            server_machine = "N/A"

        # Create the tray menu items
        self.tray_ui = TrayUI()
        self.tray_ui.create_tray_slack_ui(menu, server_status, server_machine)

        self._set_tray_display_state(running=(server_status == "Running"))

        self.tray_ui.start_server_action.triggered.connect(self._toggle_from_tray)
        self.tray_ui.stop_server_action.triggered.connect(self._toggle_from_tray)

    def _toggle_from_tray(self):
        if self.tray_ui is None:
            return

        config = SlackConfig(self.core).load_config(mode="studio")
        server_status = config["slack"]["server"].get("status")
        server_machine = config["slack"]["server"].get("machine")
        if server_status == "Running":
            if server_machine == socket.gethostname():
                ServerControls(self.core).stop_server()
                self._set_tray_display_state(running=False)
            else:
                ServerNonWarning().exec_()
        else:
            ServerControls(self.core).start_server()
            self._set_tray_display_state(running=True)

    def _set_tray_display_state(self, *, running: bool):
        if self.tray_ui is None:
            return

        stop_action = self.tray_ui.stop_server_action
        start_action = self.tray_ui.start_server_action
        status_action = self.tray_ui.status_server_action

        if running:
            stop_action.setEnabled(True)
            start_action.setEnabled(False)
            status_action.setText("Running")
            status_action.setIcon(
                QIcon(os.path.join(self.plugin_directory, "Resources", "running.png"))
            )
        else:
            stop_action.setEnabled(False)
            start_action.setEnabled(True)
            status_action.setText("Not running")
            status_action.setIcon(
                QIcon(os.path.join(self.plugin_directory, "Resources", "stopped.png"))
            )
