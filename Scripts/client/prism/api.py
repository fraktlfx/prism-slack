from Scripts.client.slack.slack_config import SlackConfig
from Scripts.client.prism.ui import InputDialog

from qtpy.QtWidgets import QDialog

studio_config = None
project_config = None
user_config = None

class API:
    def __init__(self, core):

        global studio_config, project_config, user_config

        self.core = core
        if self.is_studio_loaded() is not None:
            studio_config = SlackConfig(self.core).load_config("studio")
            project_config = SlackConfig(self.core).load_config("project")
        else:
            try:
                studio_config = SlackConfig(self.core).load_config("studio")
            except Exception:
                studio_config = None

            project_config = SlackConfig(self.core).load_config("project")
        
        user_config = SlackConfig(self.core).load_config("user")

    # Get Slack Access Token from config file
    def get_access_token(self):
        """
        Get Slack Bot Access Token from the studio configuration file.

        Returns:
            str: The Slack Bot Access Token.
        """

        return studio_config["slack"]["tokens"]["bot_token"]

    # Get Slack App Level Token from config file
    def get_app_level_token(self):
        """
        Get Slack App Level Token from the studio configuration file.

        Returns:
            str: The Slack App Level Token.
        """

        return studio_config["slack"]["tokens"]["app_token"]

    # Get the current project name
    def get_current_project(self):
        """
        Get the current project name, considering any custom Slack notification channel.

        Returns:
            str: The current project name or custom Slack channel.
        """

        custom_channel = self.get_notify_custom_channel()

        if custom_channel == "" or custom_channel is None:
            project = self.core.getConfig(
                "globals", "project_name", configPath=self.core.prismIni
            ).lower()

        else:
            project = custom_channel

        return project

    # Get Slack Notification Method from config file
    def get_notify_user_method(self):
        """
        Get Slack Notification Method from studio config file.

        Returns:
            str: The Slack notification method.
        """

        return studio_config["slack"]["notifications"]["method"]

    # Get Slack Notification User Pool from config file
    def get_notify_user_pool(self):
        """
        Get Slack Notification User Pool from studio config file.

        Returns:
            str: The Slack notification user pool.
        """

        return studio_config["slack"]["notifications"]["user_pool"]

    # Get Custom Slack Notification Channel from config file
    def get_notify_custom_channel(self):
        """
        Get Custom Slack Notification Channel from project config file.

        Returns:
            str: The custom Slack channel name.
        """

        return project_config["slack"]["custom"]["channel"]

    def get_server_status(self):
        """
        Get the current status of the Bolt server from the studio configuration file.

        Returns:
            str: The status of the Bolt server.
        """

        return studio_config["slack"]["server"]["status"]

    def get_server_machine(self):
        """
        Get the machine name where the Bolt server is running from the studio configuration file.

        Returns:
            str: The machine name of the Bolt server.
        """

        return studio_config["slack"]["server"]["machine"]

    def get_server_pid(self):
        """
        Get the process ID of the currently running Bolt server from the studio configuration file.

        Returns:
            str: The process ID of the Bolt server.
        """

        return studio_config["slack"]["server"]["pid"]

    # Get Slack Display Name from prism user configuration
    def get_prism_slack_username(self):
        """
        Return Slack username. If missing, prompt user to sign in via Slack OAuth.
        """

        user_data = SlackConfig(self.core).load_config("user")

        if user_data["slack"]["username"] == "":
            input_dialog = InputDialog(title="Enter your Slack Display Name")
            if input_dialog.exec_() == QDialog.Accepted:
                username = input_dialog.get_input()
                user_data["slack"]["username"] = username
                SlackConfig(self.core).save_config_setting(user_data, "user")
                return username

        else:
            return user_data["slack"].get("username")

    # Get Slack User ID from user list
    def get_slack_user_id(self, username, user_pool):
        """
        Get the Slack User ID based on the provided username and channel users.

        Args:
            username (str): The Slack display name of the user.
            channel_users (List[Dict[str, Any]]): The list of users in the Slack channel.

        Returns:
            str: The Slack User ID if found, None otherwise.
        """
        for user in user_pool:
            if username == user["display_name"]:
                return user.get("id")

        return None

    # Check if the studio plugin is loaded
    def is_studio_loaded(self):
        """
        Check if the Studio plugin is loaded in the core.

        Returns:
            Studio plugin instance if loaded, None otherwise.
        """

        return self.core.getPlugin("Studio")

    # Get the message to send to the user
    def get_render_message(self, slack_user, seq, shot, product, sender):
        """
        Generate a Slack message for render notification.

        Args:
            slack_user (str): The Slack user ID of the recipient.
            seq (str): The sequence identifier.
            shot (str): The shot identifier.
            product (str): The product being rendered.
            sender (str): The Slack user ID of the sender.

        Returns:
            str: The generated Slack message.
        """

        import random

        if random.randint(0, 100) == 90:
            message = f"Dearest <@{slack_user}>,\nI bring you tidings of the utmost importance! The {product} render for Shot `{shot}` in the enchanting Sequence `{seq}` has begun. Courtesy of the illustrious <@{sender}>, of course. May the pixels align in harmonious perfection!\nYours in cinematic anticipation,\nMoira Rose"

        elif random.randint(0, 100) == 100:
            message = f"<@{slack_user}>\n`{product}`/`{seq}`/`{shot}`\n<https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExeW4xNGl1dGxtMWY5d2tsMTBuYXc3enYza3FkNnpoZDNoYWlremh5NSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/SSiwN19NtD1xUAikqf/giphy.gif>"

        else:
            message = f"Heads up <@{slack_user}>!\n A new version of `{product}` for `{seq}`/`{shot}` is on the way!"

        return message