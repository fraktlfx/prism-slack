import os
import json
from copy import deepcopy


class SlackConfig:
    def __init__(self, core):
        self.core = core

    def get_slack_config(self):
        """
        Retrieve the Slack configuration file path.

        Returns:
            str: The path to the Slack configuration file.
        """

        # Get the path to the pipeline configuration file from the environment variable PRISM_STUDIO_PATH
        studio_path = os.getenv("PRISM_STUDIO_PATH")
        if studio_path:
            return os.path.join(studio_path, "configs", "slack.json")

        # If the Studio plugin is not available, check the project configuration file
        elif self.core.getPlugin("Studio") is None:
            project_config_path = self.get_project_config()

            return project_config_path

        # Get the config from the studio path
        else:
            studio_plugin = self.core.getPlugin("Studio")
            studio_path = studio_plugin.getStudioPath()

            if studio_path is None:
                project_config_path = self.get_project_config()
                return project_config_path
            else:
                return os.path.join(studio_path, "configs", "slack.json")

    def get_user_config(self):
        """
        Retrieve the Prism user configuration file path.

        Returns:
            str: The path to the Prism user configuration file.
        """

        config = self.core.configs.getConfigPath("user")

        return config

    def get_project_config(self):
        """
        Retrieve the Prism project configuration file path.

        Returns:
            str: The path to the Prism project configuration file.
        """

        user_config = self.get_user_config()
        with open(user_config, "r") as f:
            config = json.load(f)["globals"]["current project"]

        return config

    def load_config(self, mode: str):
        """
        Load the Slack configuration file based on the specified mode.

        Args:
            mode (str): The mode to determine which configuration file to load. Can be "user", "studio", or "project".

        Returns:
            dict: The data from the requested configuration file.
        """

        if mode == "user":
            config = self.get_user_config()
            with open(config, "r") as f:
                return json.load(f)

        elif mode == "studio":
            config = self.get_slack_config()

        elif mode == "project":
            config = self.get_project_config()

        else:
            self.core.popup("Cannot retrieve configuration file")
            return

        try:
            # If the pipeline file doesn't exist, create it and initialize the slack token field
            if not os.path.exists(config):
                os.makedirs(os.path.dirname(config), exist_ok=True)
                with open(config, "w") as f:
                    json.dump({"slack": {"tokens": {"bot_token": ""}}}, f, indent=4)

            # Load and read the file
            with open(config, "r") as f:
                return json.load(f)

        except Exception as e:
            print(f"Error loading config file: {e}")
            return

    def save_config_setting(self, setting: dict, mode: str):
        """
        Save the provided settings to the Slack configuration file based on the specified mode.

        Args:
            setting (dict): The settings to be saved.
            mode (str): The mode to determine which configuration file to save to. Can be "user", "studio", or "project".
        """

        if mode == "user":
            config = self.get_user_config()

        elif mode == "studio":
            config = self.get_slack_config()

        elif mode == "project":
            config = self.get_project_config()

        else:
            self.core.popup("Cannot retrieve the Slack configuration file")
            return

        try:
            if mode == "studio":
                studio = self.core.getPlugin("Studio")
                if studio is not None:
                    user = self.core.username
                    role = studio.getUserRole(user)
                    if "admin" in role:
                        with open(config, "w") as f:
                            json.dump(setting, f, indent=4)
                    else:
                        return
                else:
                    with open(config, "w") as f:
                        json.dump(setting, f, indent=4)
            else:
                with open(config, "w") as f:
                    json.dump(setting, f, indent=4)

        except Exception as e:
            print(f"Error saving config file: {e}")
            return

    def save_server_config_setting(self, setting: dict, mode: str):
        """
        Save the provided setting to the studio Slack config file based on the requested mode.

        Args:
            setting (dict): The settings to be saved.
            mode (str): The mode to determine which configuration file to save to. Can be "user", "studio", or "project".
        """

        if mode == "studio":
            config = self.get_slack_config()
        else:
            print("Cannot retrieve the Slack configuration file")
            return

        try:
            # Save the updated config
            with open(config, "w") as f:
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

        slack_defaults = {
            "tokens": {
                "bot_token": "",
                "app_token": "",
            },
            "notifications": {"method": "", "user_pool": ""},
            "custom": {"channel": ""},
            "server": {
                "status": "",
                "machine": "",
                "pid": "",
            },
        }

        try:
            if "slack" not in config:
                config["slack"] = slack_defaults
                self._set_defaults(slack_defaults, config)

            else:
                self._merge_slack_defaults(config["slack"], slack_defaults)

            self.save_config_setting(config, "studio")

        except Exception:
            return

    def _set_defaults(self, slack_defaults: dict, config: dict):
        """
        Set the default configuration options in the studio config file

        Args:
            slack_defaults (dict): The default slack configuration options
            config (dict): The loaded slack studio configuration options available.
        """

        try:
            for key, value in slack_defaults.items():
                if key not in config["slack"]:
                    config["slack"][key] = value
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_key not in config["slack"][key]:
                            config["slack"][key][sub_key] = sub_value

            # Save updated config
            self.save_config_setting(config, "studio")

        except Exception:
            self.save_config_setting(config, "studio")
            return

    def _merge_slack_defaults(self, config: dict, defaults: dict):
        """
        Merge the old slack defaults with any of the new settings.

        Args:
            config (dict): The loaded slack studio configuration options available.
            defaults (dict): The default slack configuration options
        """

        for key, value in defaults.items():
            if key not in config:
                config[key] = deepcopy(value)
            elif isinstance(value, dict) and isinstance(config[key], dict):
                self._merge_slack_defaults(config[key], value)
