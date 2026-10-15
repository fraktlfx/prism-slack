from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from prism_slack.client.prism.ui import SignInDialog, WarningDialog
from prism_slack.client.slack.slack_config import SlackConfig
from prism_slack.client.slack.slack_login import SlackLogin

from qtpy.QtWidgets import QDialog


@dataclass(frozen=True)
class _Configs:
    """
    Container for the three Slack configuration scopes.

    Prism-Slack stores settings in multiple scopes:
      - studio: shared studio-wide settings (tokens, approvals, etc.)
      - project: per-project settings (custom channel, etc.)
      - user: per-user settings (slack user id, username, etc.)
    """

    studio: Dict[str, Any]
    project: Dict[str, Any]
    user: Dict[str, Any]


class API:
    """
    Convenience API for reading/writing Prism-Slack configuration and user identity.

    This class centralizes access to Slack configuration files and small helper
    behaviors (e.g., prompting the user to sign in if their Slack identity is
    missing).

    Key design goals:
      - Avoid module-level global state: configs are cached per instance.
      - Minimize disk reads: configs are loaded once and cached, with an explicit
        `reload_configs()` method to refresh them after saving.
      - Keep existing call sites simple: preserve the existing "getter" methods.
    """

    def __init__(self, core: Any):
        """
        Initialize the API.

        Args:
            core: Prism core instance, used to access Prism plugins, global config,
                and paths required by the Slack plugin.

        Notes:
            Configs are loaded lazily and cached on first access. If you write
            a config and want the API to reflect changes immediately, call
            `reload_configs()`.
        """
        self.core = core
        self._cfg = SlackConfig(core)
        self._configs: Optional[_Configs] = None

    # -------------------------------------------------------------------------
    # Config loading / caching
    # -------------------------------------------------------------------------

    def _load_configs(self) -> _Configs:
        """
        Load and cache studio/project/user configs.

        Returns:
            A `_Configs` instance containing the loaded configuration dicts.

        Notes:
            If any config does not exist or returns `None`, it will be treated as
            an empty dict.
        """
        if self._configs is not None:
            return self._configs

        studio = self._cfg.load_config("studio") or {}
        project = self._cfg.load_config("project") or {}
        user = self._cfg.load_config("user") or {}

        self._configs = _Configs(studio=studio, project=project, user=user)
        return self._configs

    def reload_configs(self) -> None:
        """Invalidate cached configs so subsequent access reloads from disk."""
        self._configs = None

    @property
    def studio_config(self) -> Dict[str, Any]:
        """Studio-level configuration dictionary."""
        return self._load_configs().studio

    @property
    def project_config(self) -> Dict[str, Any]:
        """Project-level configuration dictionary."""
        return self._load_configs().project

    @property
    def user_config(self) -> Dict[str, Any]:
        """User-level configuration dictionary."""
        return self._load_configs().user

    # -------------------------------------------------------------------------
    # Prism integration
    # -------------------------------------------------------------------------

    def is_studio_loaded(self):
        """
        Check whether the Prism Studio plugin is loaded.

        Returns:
            The Studio plugin instance if loaded, otherwise `None`.
        """
        return self.core.getPlugin("Studio")

    def get_current_project(self) -> str:
        """
        Get the current project name, considering any custom Slack channel override.

        Returns:
            The current project name (lowercase) or the configured custom channel
            name if one is set.
        """
        custom_channel = self.get_notify_custom_channel()
        if not custom_channel:
            project = self.core.getConfig(
                "globals", "project_name", configPath=self.core.prismIni
            ).lower()
            return project
        return custom_channel

    def get_project_manager(self) -> str:
        """
        Get the project manager's name from the current project configuration.

        Returns:
            manager (str): The project manager's name if set; otherwise an empty string.
        """
        try:
            manager = self.core.getConfig("prjManagement", "manager", configPath=self.core.prismIni)
        except Exception as e:
            print(f"Error retrieving project manager from config: {e}")
            return ""

        return manager

    def get_media_status_list(self) -> list:
        """
        Get a list of media statuses from the current project configuration.

        Returns:
            statuses (list): List of media statuses with their abbreviations if set; otherwise an empty list.
        """
        try:
            if self.core.getPlugin("ProjectManagement") is None:
                return []
            status_list_dict = self.core.getConfig(
                "prjManagement", "prism_status", configPath=self.core.prismIni
            )
            status_list = []
            for s in status_list_dict:
                status = {}
                if s.get("media") is True:
                    status["name"] = s.get("name", "")
                    status["abbreviation"] = s.get("abbreviation", "")
                    status_list.append(status)

            return status_list

        except Exception as e:
            print(f"Error retrieving media status list from config: {e}")
            return []

    def get_version_folder(self, file_path: str) -> Path:
        """
        Given the first file of a prism sequence, determine the correct version folder.
        Handles:
        - v0005 (mp4)
        - v0005 (mov)
        - v0005 (proxy)
        - v0005
        - render cases where the version folder is one level up
        Works on Windows and Linux.
        """
        p = Path(file_path).resolve()
        p = Path(str(p).replace("\\", "/"))
        print(f"Resolving version folder for file: {p}")

        parent = p.parent
        grandparent = parent.parent

        def is_version(name: str) -> bool:
            return name.startswith("v") and name[1:].isdigit()

        if is_version(parent.name):
            return parent

        if "(" in parent.name and parent.name.endswith(")"):
            cleaned = parent.name.split(" ")[0]
            if is_version(cleaned):
                return parent.with_name(cleaned)

        if is_version(grandparent.name):
            return grandparent

        if "(" in grandparent.name and grandparent.name.endswith(")"):
            cleaned = grandparent.name.split(" ")[0]
            if is_version(cleaned):
                return grandparent.with_name(cleaned)

        return parent

    # -------------------------------------------------------------------------
    # Slack tokens / IDs
    # -------------------------------------------------------------------------

    def get_user_access_token(self) -> str:
        """
        Get the Slack user access token from the user configuration.

        Returns:
            The Slack user access token if set; otherwise an empty string.
        """
        user_data = self.user_config
        slack = user_data.get("slack", {})
        return slack.get("user_token", "")

    def get_access_token(self) -> str:
        """
        Get Slack Bot Access Token from the studio configuration.

        Returns:
            The Slack Bot Access Token.
        """
        return self.studio_config["slack"]["tokens"]["bot_token"]

    def get_client_id(self) -> str:
        """
        Get Slack Client ID from the studio configuration.

        Returns:
            The Slack Client ID.
        """
        return self.studio_config["slack"]["tokens"]["client_id"]

    def get_client_secret(self) -> str:
        """
        Get Slack Client Secret from the studio configuration.

        Returns:
            The Slack Client Secret.
        """
        return self.studio_config["slack"]["tokens"]["client_secret"]

    def get_app_level_token(self) -> str:
        """
        Get Slack App Level Token from the studio configuration.

        Returns:
            The Slack App Level Token.
        """
        return self.studio_config["slack"]["tokens"]["app_token"]

    def get_prism_slack_username(self) -> str:
        """
        Return the Slack username for the current user.

        If the username and user_id are missing, this prompts the user to sign in
        via Slack OAuth and persists the result into the user config.

        Returns:
            The Slack username if available or successfully retrieved; otherwise
            an empty string.
        """
        user_data = self.user_config
        slack = user_data.get("slack", {})

        username = slack.get("username", "")
        user_id = slack.get("user_id", "")

        if username and user_id:
            return username

        def login():
            return SlackLogin(self.get_client_id(), self.get_client_secret()).login()

        dlg = SignInDialog(login)
        if dlg.exec_() != QDialog.Accepted or not getattr(dlg, "result_user", None):
            return ""

        slack_user = dlg.result_user
        slack["username"] = slack_user.get("name", "")
        slack["user_id"] = slack_user.get("id", "")
        user_data["slack"] = slack

        self._cfg.save_config_setting(user_data, "user")
        self.reload_configs()

        return slack["username"]

    def get_prism_slack_user_id(self) -> Optional[str]:
        """
        Get Slack User ID from the user configuration.

        Returns:
            The Slack user ID if set; otherwise `None`.
        """
        user_data = self.user_config
        slack = user_data.get("slack", {})
        user_id = slack.get("user_id") or ""
        return user_id or None

    def get_slack_user_id(self, username: str, channel_users: List[Dict[str, Any]]):
        """
        Get a Slack user ID from a list of channel users by display name.

        Args:
            username: Slack display name to match against each user's "display_name".
            channel_users: List of Slack users (dicts), each expected to include keys
                like "display_name" and "id".

        Returns:
            Slack user ID if found, otherwise `None`.
        """
        for user in channel_users:
            if username == user.get("display_name"):
                return user.get("id")
        return None

    # -------------------------------------------------------------------------
    # Notifications / approvals / server settings
    # -------------------------------------------------------------------------

    def get_tag_artist(self) -> bool:
        """
        Get whether tagging the artist on publish to Slack is enabled.

        Returns:
            True if tagging is enabled, False otherwise.
        """
        return self.studio_config["slack"]["notifications"]["tag_artist"]

    def get_notify_user_method(self) -> str:
        """
        Get Slack notification method from studio config.

        Returns:
            Notification method string.
        """
        return self.studio_config["slack"]["notifications"]["method"]

    def get_notify_user_pool(self) -> str:
        """
        Get Slack notification user pool from studio config.

        Returns:
            User pool string.
        """
        return self.studio_config["slack"]["notifications"]["user_pool"]

    def get_notify_custom_channel(self) -> str:
        """
        Get custom Slack notification channel from project config.

        Returns:
            Custom channel name, or an empty string if not set.
        """
        return self.project_config["slack"]["custom"]["channel"]

    def get_server_approvals(self) -> bool:
        """
        Get whether approvals are enabled.

        Returns:
            True if approvals are enabled, False otherwise.
        """
        return self.studio_config["slack"]["approvals"]["enabled"]

    def get_approvals_usergroup_status(self) -> bool:
        """
        Get whether approvals use Slack usergroups.

        Returns:
            True if using usergroups, False otherwise.
        """
        return self.studio_config["slack"]["approvals"]["enable_usergroup"]

    def get_approvals_update_status(self) -> bool:
        """
        Get whether the plugin should update media status to "In Progress" or "To Review" on publish.

        Returns:
            True if the plugin should update media status, False otherwise.
        """
        return self.studio_config["slack"]["approvals"]["update_status"]

    def get_approvals_usergroup(self) -> str:
        """
        Get Slack usergroup id used for approvals.

        Returns:
            Usergroup id string.
        """
        return self.studio_config["slack"]["approvals"]["usergroup"]

    def get_server_status(self) -> str:
        """
        Get Bolt server status from studio config.

        Returns:
            Server status string.
        """
        return self.studio_config["slack"]["server"]["status"]

    def get_server_machine(self) -> str:
        """
        Get Bolt server machine name from studio config.

        Returns:
            Machine name string.
        """
        return self.studio_config["slack"]["server"]["machine"]

    def get_server_pid(self) -> str:
        """
        Get Bolt server process id from studio config.

        Returns:
            PID string.
        """
        return self.studio_config["slack"]["server"]["pid"]

    # -------------------------------------------------------------------------
    # UI helpers
    # -------------------------------------------------------------------------

    def teams_user_warning(self, user: str) -> bool:
        """
        Show a warning dialog if a user is on the team but not part of the project.

        Args:
            user: Slack username.

        Returns:
            True if the user accepts the warning, False otherwise.
        """
        dialog = WarningDialog(team_user=user)
        return dialog.exec_() == QDialog.Accepted

    # -------------------------------------------------------------------------
    # Message helpers
    # -------------------------------------------------------------------------

    def get_render_message(
        self,
        slack_user: str,
        product: str,
        sender: str,
        asset: str = None,
        seq: str = None,
        shot: str = None,
    ) -> str:
        """
        Generate a Slack message for render notification.

        Args:
            slack_user: Slack user ID of the recipient.
            seq: Sequence identifier.
            shot: Shot identifier.
            product: Product being rendered.
            sender: Slack user ID of the sender.

        Returns:
            A Slack-formatted message string.
        """
        import random

        if asset is not None:
            return f"Hey <@{slack_user}>! A new version of `{product}` for asset `{asset}` is on the way!"

        roll = random.randint(0, 100)
        if roll == 90:
            return (
                f"Dearest <@{slack_user}>,\n"
                f"I bring you tidings of the utmost importance! The {product} render for "
                f"Shot `{shot}` in the enchanting Sequence `{seq}` has begun. "
                f"Courtesy of the illustrious <@{sender}>, of course. "
                f"May the pixels align in harmonious perfection!\n"
                "Yours in cinematic anticipation,\n"
                "Moira Rose"
            )

        if roll == 100:
            return (
                f"<@{slack_user}>\n"
                f"`{product}`/`{seq}`/`{shot}`\n"
                "<https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExeW4xNGl1dGxtMWY5d2tsMTBuYXc3enYza3FkNnpoZDNoYWlremh5NSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/SSiwN19NtD1xUAikqf/giphy.gif>"
            )

        return f"Heads up <@{slack_user}>!\n A new version of `{product}` for `{seq}`/`{shot}` is on the way!"

    # -------------------------------------------------------------------------
    # Licensing
    # -------------------------------------------------------------------------

    def get_license_key(self) -> str:
        """
        Get the license key information from studio config.

        Returns:
            License key string.
        """
        return self.studio_config["slack"]["subscription"]["license_key"]

    def get_license_email(self) -> str:
        """
        Get the license email information from studio config.

        Returns:
            License email string.
        """
        return self.studio_config["slack"]["subscription"]["email"]

    def get_license_product_id(self) -> str:
        """
        Get the product ID associated with the license from studio config.

        Returns:
            Product ID string.
        """
        return self.studio_config["slack"]["subscription"]["product_id"]
