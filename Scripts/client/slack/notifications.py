import os

from client.prism.utils import log_and_print

from Scripts.client.slack.slack_config import SlackConfig
from Scripts.client.prism.api import API
from Scripts.client.slack.api import (
    get_channel_users,
    get_channel_id,
    post_channel_message,
    post_direct_message,
    post_channel_ephemeral_message,
    post_direct_ephemeral_message,
)
from Scripts.client.prism.ui import InputDialog


def notify_before_publish(core: object, notify_user: str, product: str):
    try:
        access_token = API(core).get_access_token()
    except Exception as e:
        log_and_print(40, f"Failed to retrieve Slack access token. Error: {e}")
        raise Exception(
            "Failed to retrieve Slack access token. Please check your configuration."
        )

    if API(core).get_prism_slack_username() == "":
        local_user = _input_local_slack_user()

    else:
        local_user = API(core).get_prism_slack_username()

    project = API(core).get_current_project()
    channel = get_channel_id(access_token, project)
    channel_users = get_channel_users(access_token, channel)
    slack_recipient = API(core).get_slack_user_id(notify_user, channel_users)
    slack_sender = API(core).get_slack_user_id(local_user, channel_users)

    log_and_print(
        20,
        f"""Collected information for Slack notification:
                Slack Recipient: {slack_recipient}
                Channel: {channel}
                Product: {product}
                Slack Sender: {slack_sender}
                """,
    )

    _notify_slack_user(
        core, access_token, slack_recipient, channel, product, slack_sender
    )


def _notify_slack_user(
    core: object,
    access_token: str,
    slack_recipient: str,
    channel: str,
    product: str,
    slack_sender: str,
):
    """
    Notify the slack user about new render/playblast/export is on the way

    Args:
        core (Any): The core application object
        access_token (str): Slack access token
        slack_recipient (str): Slack user ID of the recipient
        channel (str): Slack channel ID
        product (str): Name of the product being rendered
        slack_sender (str): Slack user ID of the sender
    """
    if os.getenv("PRISM_SEQUENCE") is not None:
        seq = os.getenv("PRISM_SEQUENCE")
        shot = os.getenv("PRISM_SHOT")

    message = API(core).get_message(slack_recipient, seq, shot, product, slack_sender)

    config = SlackConfig(core).load_config("studio")
    method = config["slack"]["notifications"].get("method")

    if method.lower() == "channel":
        post_channel_message(access_token, channel, message)

    elif method.lower() == "direct":
        post_direct_message(access_token, slack_recipient, message)

    elif method.lower() == "ephemeral direct":
        post_direct_ephemeral_message(access_token, slack_recipient, message)

    else:
        post_channel_ephemeral_message(access_token, slack_recipient, channel, message)


def _input_local_slack_user() -> str:
    dialog = InputDialog(title="Enter your Slack Display Name")
    dialog.exec_()

    return dialog.get_input()
