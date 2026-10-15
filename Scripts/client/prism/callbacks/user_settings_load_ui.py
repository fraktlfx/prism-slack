from prism_slack.client.prism.api import API
from prism_slack.client.prism.ui.settings_ui import SettingsUI
from prism_slack.client.slack.slack_config import SlackConfig
from prism_slack.client.slack.slack_login import SlackLogin
from prism_slack.client.slack.api.post import post_signout_slack

from qtpy.QtWidgets import QWidget

_slack_login_in_progress = False


def userSettings_loadUI(core: object, origin: QWidget):
    """
    Load the Slack UI in the user settings window.

    Args:
        core (object): The core application object.
        origin (QWidget): The origin object (user settings window).
    """

    SettingsUI(core).create_user_settings_ui(origin)

    if not hasattr(origin, "_slot_slack_signin"):
        origin._slot_slack_signin = lambda: _slack_signin(core, origin)

    if not hasattr(origin, "_slot_slack_signout"):
        origin._slot_slack_signout = lambda: _slack_signout(core, origin)

    if not hasattr(origin, "_slack_auth_connected"):
        origin.b_slack_signin.clicked.connect(origin._slot_slack_signin)
        origin.b_slack_signout.clicked.connect(origin._slot_slack_signout)
        origin._slack_auth_connected = True

    _check_username(core, origin)


def _set_auth_button_state(origin: QWidget, signed_in: bool, username: str = ""):
    """
    Set auth button signal connections and UI state.

    Args:
        origin (QWidget): The origin object (user settings window).
        signed_in (bool): Whether user is signed in.
        username (str): Slack username to display when signed in.
    """

    if signed_in:
        origin.b_slack_signin.setText(f"Signed in as {username}")
        origin.b_slack_signin.setEnabled(False)
        origin.b_slack_signout.setVisible(True)
        origin.b_slack_signout.setEnabled(True)
    else:
        origin.b_slack_signin.setText("Sign in with Slack")
        origin.b_slack_signin.setEnabled(True)
        origin.b_slack_signout.setVisible(False)


def _check_username(core: object, origin: QWidget):
    """
    Check and set the Slack display name in the user settings window.

    Args:
        core (object): The core application object.
        origin (QWidget): The origin object (user settings window).
    """

    user_data = SlackConfig(core).load_config("user")

    if "slack" not in user_data:
        user_data["slack"] = {}
    if "username" not in user_data["slack"]:
        user_data["slack"]["username"] = ""
    if "user_id" not in user_data["slack"]:
        user_data["slack"]["user_id"] = ""
    if "user_token" not in user_data["slack"]:
        user_data["slack"]["user_token"] = ""

    username = user_data["slack"].get("username") or ""
    user_id = user_data["slack"].get("user_id") or ""

    if user_id:
        _set_auth_button_state(origin, signed_in=True, username=username)
    else:
        _set_auth_button_state(origin, signed_in=False)

    SlackConfig(core).save_config_setting(user_data, "user")


def _slack_signin(core: object, origin: QWidget):
    """
    Handle the Slack sign-in process from the user settings window.

    Args:
        core (object): The core application object.
        origin (QWidget): The origin object (user settings window).
    """

    global _slack_login_in_progress

    if _slack_login_in_progress:
        return

    _slack_login_in_progress = True

    try:
        client_id = API(core).get_client_id()
        client_secret = API(core).get_client_secret()

        if not client_id or not client_secret:
            core.popup(
                "Slack client ID or secret are not configured in the settings. Please set them up and then try again."
            )
            return

        slack_user = SlackLogin(client_id, client_secret).login()
        if not slack_user:
            return

        user_id = slack_user.get("id")
        username = slack_user.get("name") or ""
        user_token = slack_user.get("token")
        if not user_id:
            core.popup("Slack sign-in failed: no user id returned.")
            return
        print(
            "Acquired User ID: ",
            user_id,
            " || Acquired Display Name: ",
            username,
            " || Acquired Token: ",
            user_token,
        )

        user_data = SlackConfig(core).load_config("user")
        if "slack" not in user_data:
            user_data["slack"] = {}
        user_data["slack"]["user_id"] = user_id
        user_data["slack"]["username"] = username
        user_data["slack"]["user_token"] = user_token

        print("Saving user info to config")
        SlackConfig(core).save_config_setting(user_data, "user")

        print("Setting Sign-in with Slack button text to Signed in as " + username)
        _set_auth_button_state(origin, signed_in=True, username=username)

    finally:
        _slack_login_in_progress = False


def _slack_signout(core: object, origin: QWidget):
    """
    Handle the Slack sign-out process from the user settings window.

    Args:
        core (object): The core application object.
        origin (QWidget): The origin object (user settings window).
    """

    user_access_token = API(core).get_user_access_token()
    post_signout_slack(user_access_token)

    user_data = SlackConfig(core).load_config("user")
    if "slack" not in user_data:
        user_data["slack"] = {}
    user_data["slack"]["user_id"] = ""
    user_data["slack"]["username"] = ""
    user_data["slack"]["user_token"] = ""

    print("Clearing user info from config")
    SlackConfig(core).save_config_setting(user_data, "user")

    print("Setting Sign-in with Slack button text to Sign in with Slack")
    _set_auth_button_state(origin, signed_in=False)

    core.popup("You have been signed out of Slack.", title="Slack")
