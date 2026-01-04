import os
import platform
import socket
from pathlib import Path
from typing import Any

from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from qtpy.QtWidgets import QDialog

from Scripts.client.prism.api import API
from Scripts.client.prism.ui import (
    ServerNonWarning,
    ServerStartWarning,
    ServerStopWarning,
)
from Scripts.client.slack.slack_config import SlackConfig


class ServerControls:
    """Class to manage Slack Bolt Server controls."""

    def __init__(self, core):
        self.core = core

    @err_catcher(name=__name__)
    def start_server(self):
        """
        Start the Slack Bolt Server. This works from the console commands.
        """

        import subprocess

        # Create paths for the environment variables to be used in the Slack Bolt Server
        scripts_path = self.core.getPlugin("Slack").pluginDirectory
        bolt_path = os.path.join(scripts_path, "server", "bolt.py")

        config = SlackConfig(self.core).load_config(mode="studio")
        token = API(self.core).get_access_token()
        app_token = API(self.core).get_app_level_token()

        python_version = self.core.pythonVersion
        if platform.system() == "Windows":
            executable = os.path.join(self.core.prismLibs, f"{python_version}", "python.exe")
        else:
            executable = os.path.join(self.core.prismLibs, f"{python_version}", "bin", "python")

        # Set the environment variables for the Slack Bolt Server
        sub_env = os.environ.copy()
        sub_env["BOLTPATH"] = f"{Path(__file__).resolve().parents[2]}/PythonLibs"
        sub_env["SCRIPTSPATH"] = f"{Path(__file__).resolve().parents[1]}"
        sub_env["PRISMPATH"] = f"{self.core.prismLibs}/PythonLibs/Python3"
        sub_env["PRISM_CORE"] = f"{self.core.prismLibs}/Scripts"
        sub_env["PRISM_UTILS"] = f"{self.core.prismLibs}/Scripts/PrismUtils"

        server_status = config["slack"]["server"].get("status")

        # Set handler for console events to reset the server status if the server is stopped
        if platform.system() == "Windows":
            try:
                import win32api

                win32api.SetConsoleCtrlHandler(
                    lambda event: (self.reset_server_status() if event == 2 else False), True
                )

            except Exception as e:
                print(f"Error setting console control handler: {e}")

        else:
            import signal

            def handle_signal(signum, frame):
                self.reset_server_status()
                raise SystemExit("Slack Bolt Server stopped")

            signal.signal(signal.SIGINT, handle_signal)
            signal.signal(signal.SIGTERM, handle_signal)
            signal.signal(signal.SIGHUP, handle_signal)

        # Attempt to start the Slack Bolt Server
        try:
            server_status = config["slack"]["server"].get("status")
            if server_status != "Running" and os.path.exists(bolt_path):
                print("Starting the Slack Bolt Server")
                bolt = subprocess.Popen(
                    [executable, bolt_path, token, app_token], env=sub_env, text=True
                )

                # Update the server status/machine/pid in the config file
                config = SlackConfig(self.core).load_config(mode="studio")
                config["slack"]["server"]["status"] = "Running"
                config["slack"]["server"]["machine"] = socket.gethostname()
                config["slack"]["server"]["pid"] = bolt.pid
                SlackConfig(self.core).save_server_config_setting(config, mode="studio")

            else:
                print("Slack Bolt Server is already running")
                return

        except Exception as e:
            self.core.popup(f"Error starting the Slack Bolt Server: {e}")
            self.stop_server()

        plugin = self.core.getPlugin("Slack")
        handler = getattr(plugin, "tray_handler", None)
        if handler is not None:
            handler._set_tray_display_state(running=True)

    def reset_server_status(self):
        """
        Reset the Slack Bolt Server status in the configuration file.
        """

        config = SlackConfig(self.core).load_config(mode="studio")
        config["slack"]["server"]["status"] = ""
        config["slack"]["server"]["machine"] = ""
        config["slack"]["server"]["pid"] = ""
        SlackConfig(self.core).save_server_config_setting(config, mode="studio")

    @err_catcher(name=__name__)
    def stop_server(self):
        """
        Stop the Slack Bolt Server. This works from the console commands.
        """

        config = SlackConfig(self.core).load_config(mode="studio")
        status = config["slack"]["server"].get("status")
        pid = config["slack"]["server"].get("pid")

        if status == "Running":
            try:
                if os.name == "nt":
                    os.system(f"taskkill /F /PID {pid}")
                    print("Slack Bolt Server stopped")
                    self.reset_server_status()

                if platform.system() != "Windows":
                    os.system(f"kill -9 {pid}")
                    print("Slack Bolt Server stopped")
                    self.reset_server_status()

            except Exception as e:
                print(f"Error stopping the Slack Bolt Server: {e}")

        plugin = self.core.getPlugin("Slack")
        handler = getattr(plugin, "tray_handler", None)
        if handler is not None:
            handler._set_tray_display_state(running=False)

    @err_catcher(name=__name__)
    def gui_start_server(self, origin: Any):
        """
        Start the Slack Bolt Server from the GUI.

        Args:
            origin (Any): The origin object containing the GUI elements.
        """

        start_check = ServerStartWarning()
        if start_check.exec_() == QDialog.Accepted:
            self.start_server()
            origin.b_server.setText("Stop Server")
            origin.b_reset_server.setEnabled(False)
            self.check_server_status(origin)
        else:
            return

    @err_catcher(name=__name__)
    def gui_stop_server(self, origin: Any):
        """
        Stop the Slack Bolt Server from the GUI.

        Args:
            origin (Any): The origin object containing the GUI elements.
        """

        stop_check = ServerStopWarning()
        if stop_check.exec_() == QDialog.Accepted:
            self.stop_server()
            origin.b_server.setText("Start Server")
            origin.b_reset_server.setEnabled(True)
            self.check_server_status(origin)
        else:
            return

    @err_catcher(name=__name__)
    def gui_reset_server_status(self, origin: Any):
        """
        Reset the Slack Bolt Server status from the GUI.

        Args:
            origin (Any): The origin object containing the GUI elements.
        """

        self.reset_server_status()
        origin.b_server.setText("Start Server")
        origin.b_reset_server.setEnabled(False)
        self.check_server_status(origin)

    @err_catcher(name=__name__)
    def check_server_status(self, origin: Any):
        """
        Check the status of the Slack Bolt Server and update the GUI accordingly.

        Args:
            origin (Any): The origin object containing the GUI elements.

        Returns:
            str: The current status of the Slack Bolt Server.
        """

        config = SlackConfig(self.core).load_config(mode="studio")

        status = config["slack"]["server"].get("status")
        machine = config["slack"]["server"].get("machine")

        if origin is not None and status == "Running":
            origin.l_server_status_value.setText(status)
            origin.l_machine_value.setText(machine)
            origin.b_server.setText("Stop Server")
        else:
            origin.l_server_status_value.setText("Not running")
            origin.l_machine_value.setText("")
            origin.b_server.setText("Start Server")

        return config["slack"]["server"].get("status")

    @err_catcher(name=__name__)
    def toggle_server(self, origin: Any):
        """
        Toggle the Slack Bolt Server based on its current status.

        Args:
            origin (Any): The origin object containing the GUI elements.
        """

        config = SlackConfig(self.core).load_config(mode="studio")

        server_machine = config["slack"]["server"].get("machine")
        server_status = config["slack"]["server"].get("status")

        if server_status == "Running":
            if socket.gethostname() != server_machine:
                non_server_check = ServerNonWarning()
                non_server_check.exec_()
                return
            else:
                self.gui_stop_server(origin)
        else:
            origin.b_reset_server.setEnabled(True)
            self.gui_start_server(origin)
