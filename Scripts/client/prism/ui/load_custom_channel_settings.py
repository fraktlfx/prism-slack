import os
from pathlib import Path

from prism_slack.client.prism.api import API
from prism_slack.client.prism.utils import log_and_print
from prism_slack.client.slack.api.get import get_channel_id
from prism_slack.client.slack.slack_config import SlackConfig

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QWidget


def load_custom_channel_settings(core: object, origin: QWidget):
    _check_custom_channel(core, origin)
    _connect_events(core, origin)


def _connect_events(core: object, origin: QWidget):
    origin.b_custom_channel_verify.clicked.connect(
        lambda: _handle_custom_channel_click(core, origin)
    )


def _handle_custom_channel_click(core: object, origin: QWidget):
    if origin.b_custom_channel_verify.text() == "Clear":
        _clear_custom_channel(core, origin)
        return

    _verify_custom_channel(core, origin)


def _set_custom_channel_status(origin: QWidget, verified: bool):
    plugin_directory = Path(__file__).resolve().parents[4]
    icon_name = "running.png" if verified else "not_verified.png"
    button_text = "Clear" if verified else "Verify"

    origin.b_custom_channel_verify.setText(button_text)
    origin.le_custom_channel_action.setIcon(
        QIcon(os.path.join(plugin_directory, "Resources", icon_name))
    )


def _check_custom_channel(core: object, origin: QWidget):
    """
    Checks if a custom channel is already saved in the config file and updates the UI accordingly.
    If no custom channel is saved, it sets the placeholder text for the input field.
    Args:
        core (object): The PrismCore instance.
        origin (QWidget): The QWidget that contains the custom channel input field and verify button, used to update the verification status in the UI.
    """
    config = SlackConfig(core).load_config(mode="project")
    if "slack" not in config:
        config["slack"] = {}
        SlackConfig(core).save_config_setting(config, mode="project")

    if "custom" not in config["slack"]:
        config["slack"]["custom"] = {}
        config["slack"]["custom"]["channel"] = ""
        SlackConfig(core).save_config_setting(config, mode="project")

        origin.le_custom_channel.setPlaceholderText("Enter a custom channel")

    custom_channel = API(core).get_notify_custom_channel()

    if custom_channel != "":
        origin.le_custom_channel.setText(custom_channel)
        _set_custom_channel_status(origin, verified=True)

    else:
        origin.le_custom_channel.setPlaceholderText("Enter a custom channel")
        _set_custom_channel_status(origin, verified=False)


# Verify the custom channel exists on Slack
def _verify_custom_channel(core: object, origin: QWidget):
    """
    Verifies the custom channel and saves its name and channel id to the project pipeline.json file if it is valid and exists.
    If the field is empty it and the user presses the button, it will clear the custom channel info from the config file and set the verification status to "Not Verified".

    Args:
        core (object): The PrismCore instance.
        origin (QWidget): The QWidget that contains the custom channel input field and verify button, used to update the verification status in the UI.
    """
    custom_channel = origin.le_custom_channel.text().lower()
    log_and_print(20, f"Verifying custom channel: {custom_channel}")

    if custom_channel == "":
        _set_custom_channel_status(origin, verified=False)
        return

    token = API(core).get_access_token()
    if token != "":
        channel_id = get_channel_id(access_token=token, project_name=custom_channel)
        log_and_print(20, f"Channel ID for '{custom_channel}': {channel_id}")

        if channel_id is not None:
            origin.le_custom_channel.setText(custom_channel)
            _set_custom_channel_status(origin, verified=True)

            # -----------
            # Save the custom channel and channel ID to the config file
            # -----------
            config = SlackConfig(core).load_config(mode="project")
            if "slack" not in config:
                config["slack"] = {}

            if "custom" not in config["slack"]:
                config["slack"]["custom"] = {}

            config["slack"]["custom"]["channel"] = custom_channel
            config["slack"]["custom"]["channel_id"] = channel_id

            SlackConfig(core).save_config_setting(config, mode="project")

        else:
            core.popup(
                "The Slack plugin couldn't verify the custom channel, double check your channel name and try again. If your channel is private please verify the Prism app is accessible to the channel you are trying to use."
            )
            log_and_print(
                40,
                f"Failed to verify custom channel: {custom_channel}. Channel not found either because it doesn't exist or the Prism app doesn't have access to it.",
            )
    else:
        core.popup("No access token found. Please input it in your settings first.")


def _clear_custom_channel(core: object, origin: QWidget):
    """
    Clears the custom channel info from the config file and resets the verification status in the UI.

    Args:
        core (object): The PrismCore instance.
        origin (QWidget): The QWidget that contains the custom channel input field and verify button, used to update the verification status in the UI.
    """
    _set_custom_channel_status(origin, verified=False)
    origin.le_custom_channel.setText("")

    config = SlackConfig(core).load_config(mode="project")
    config["slack"]["custom"]["channel"] = ""
    config["slack"]["custom"]["channel_id"] = ""
    SlackConfig(core).save_config_setting(config, mode="project")
