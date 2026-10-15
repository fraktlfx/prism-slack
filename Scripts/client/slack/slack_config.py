import os
import json
from copy import deepcopy
from pathlib import Path
from typing import Mapping


class SlackModeError(Exception):
    """Custom exception for invalid Slack mode errors."""

    pass


class SlackConfig:
    def __init__(self, core: object):
        self.core = core

    @property
    def slack_defaults(self) -> dict:
        """
        Default Slack configuration options. Factory that returns a new dictionary each time so
        that modifications to the returned dictionary do not have weird side effects elsewhere.
        """
        return {
            "tokens": {
                "bot_token": "",
                "client_id": "",
                "client_secret": "",
                "app_token": "",
            },
            "notifications": {"tag_artist": False, "method": "", "user_pool": ""},
            "custom": {"channel": ""},
            "approvals": {
                "enabled": False,
                "update_status": False,
                "enable_usergroup": False,
                "usergroup": "",
            },
            "server": {
                "status": "",
                "machine": "",
                "pid": "",
            },
        }

    def get_slack_config_path(self) -> str:
        """
        Retrieve the Slack configuration file path.

        Returns:
            slack_config_path (str): The path to the Slack configuration file.
        """

        slack_config_path = os.getenv("PRISM_SLACK_CONFIG_PATH")
        studio_path = os.getenv("PRISM_STUDIO_PATH")
        studio_enabled = self.core.getPlugin("Studio")

        config_path = ""

        if slack_config_path:
            config_path = os.path.join(slack_config_path, "slack.json")

        elif studio_path:
            config_path = os.path.join(studio_path, "configs", "slack.json")

        elif studio_enabled is not None:
            studio_path = studio_enabled.getStudioPath()
            if studio_path:
                config_path = os.path.join(studio_path, "configs", "slack.json")
            else:
                config_path = self.get_project_config_path()

        else:
            config_path = self.get_project_config_path()

        return config_path

    def get_user_config_path(self):
        """
        Retrieve the Prism user configuration file path.

        Returns:
            user_path (str): The path to the Prism user configuration file.
        """

        return self.core.configs.getConfigPath("user")

    def get_project_config_path(self) -> str:
        """
        Retrieve the Prism project configuration file path.

        Returns:
            project_path (str): The path to the Prism project configuration file.
        """
        project_path = self.core.configs.getConfig(
            "globals", "current project", config="user", dft=""
        )
        project_path = (project_path or "").strip()
        if not project_path:
            return ""

        project_path = str(Path(project_path).expanduser())

        # Validate project still exists
        if not Path(project_path).exists():
            # project is stale; clear it so Prism stops trying to load it
            self.core.configs.setConfig("globals", "current project", "", config="user")
            self.core.configs.clearCache(self.core.userini)
            return ""

        return project_path

    def _get_config_path(self, mode: str) -> str:
        """
        Retrieve the configuration file path based on the specified mode.

        Args:
            mode (str): The mode to determine which configuration file path to retrieve.
                Can be "user", "studio", or "project".

        Returns:
            path (str): The path to the requested configuration file.
        """

        path = ""
        if mode == "user":
            path = self.get_user_config_path()

        elif mode == "studio":
            path = self.get_slack_config_path()

        elif mode == "project":
            path = self.get_project_config_path()
        else:
            raise SlackModeError(f"Invalid mode {mode!r} specified.")

        return path

    def load_config(self, mode: str) -> dict:
        """
        Load the Slack configuration file based on the specified mode.

        If the configuration file does not exist, it will be created with default settings.

        Args:
            mode (str): The mode to determine which configuration file to load.
                Can be "user", "studio", or "project".

        Returns:
            dict: The data from the requested configuration file.
        """

        config_path = self._get_config_path(mode)

        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                json.dump({"slack": self.slack_defaults}, f, indent=4)

        with open(config_path, "r") as f:
            config_data = json.load(f)

        try:
            previous_slack_config = config_data.get("slack", {})
            # Merge with defaults to ensure all keys are present
            full_slack_config = self._deep_merge_dictionaries(
                self.slack_defaults, previous_slack_config
            )
            config_data["slack"] = full_slack_config
            return config_data

        except Exception as e:
            print(
                f"Error loading Slack configuration from {config_path!r}: {e}. Using defaults."
            )
            config_data["slack"] = self.slack_defaults
            return config_data

    def save_config_setting(self, setting: dict, mode: str):
        """
        Save the provided settings to the Slack configuration file based on the specified mode.

        Args:
            setting (dict): The settings to be saved.
            mode (str): The mode to determine which configuration file to save to.
                Can be "user", "studio", or "project".
        """

        try:
            config_path = self._get_config_path(mode)
        except SlackModeError:
            self.core.popup(
                f"Invalid mode {mode!r} specified for saving config. Aborting save."
            )
            return

        if not os.path.exists(config_path):
            print(
                f"Cannot retrieve the Slack configuration file at {config_path!r}. Aborting save."
            )
            return

        try:
            if mode == "studio":
                studio = self.core.getPlugin("Studio")
                if studio is not None:
                    user = self.core.username
                    role = studio.getUserRole(user)
                    if "admin" in role:
                        with open(config_path, "w") as f:
                            json.dump(setting, f, indent=4)
                    else:
                        self.core.popup(
                            "You do not have permission to modify the Slack studio configuration."
                        )
                        return
                else:
                    with open(config_path, "w") as f:
                        json.dump(setting, f, indent=4)
            else:
                with open(config_path, "w") as f:
                    json.dump(setting, f, indent=4)

        except Exception as e:
            print(f"Error saving config file: {e}")
            return

    def save_server_config_setting(self, setting: dict, mode: str):
        """
        Save the provided setting to the studio Slack config file based on the requested mode.

        Args:
            setting (dict): The settings to be saved.
            mode (str): The mode to determine which configuration file to save to.
                Can be "user", "studio", or "project".
        """

        if mode == "studio":
            config_path = self.get_slack_config_path()
        else:
            print("Cannot retrieve the Slack configuration file")
            return

        try:
            # Save the updated config
            with open(config_path, "w") as f:
                json.dump(setting, f, indent=4)

        except Exception as e:
            print(f"Error saving server config file: {e}")
            return

    def check_slack_studio_options(self, config: dict):
        """
        Check if the slack studio config contains the defaults.

        Args:
            config (dict): The loaded configuration file that is being checked.
        """

        try:
            config["slack"] = self._deep_merge_dictionaries(
                source=self.slack_defaults, destination=config.get("slack", {})
            )
            if "tag_artist" not in config["slack"]["notifications"]:
                config["slack"]["notifications"]["tag_artist"] = False

            if "update_status" not in config["slack"]["approvals"]:
                config["slack"]["approvals"]["update_status"] = False

            self.save_config_setting(config, "studio")

        except Exception as e:
            self.core.popup(f"Error checking Slack studio configuration options. {e}")
            return

    def _deep_merge_dictionaries(self, source: Mapping, destination: dict):
        """
        Merge the old slack defaults with any of the new settings.

        Args:
            config (dict): The loaded slack studio configuration options available.
            defaults (dict): The default slack configuration options

        Returns:
            destination (dict): The merged dictionary with all the necessary keys and values.
        """
        for key, value in source.items():
            if key not in destination:
                destination[key] = deepcopy(value)
            else:
                if isinstance(value, Mapping) and isinstance(destination[key], Mapping):
                    self._deep_merge_dictionaries(value, destination[key])
        return destination
