import os

from prism_slack.client.prism.utils.logging import log_and_print

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


def notify_before_publish(core: object, notify_user: str, product: str):
    """
    Handle the common notification setup logic.

    Args:
        core (object): The core application object
        notify_user (str): Display name of the user to notify
        product (str): Name of the product being rendered
    """
    try:
        access_token = API(core).get_access_token()
    except Exception as e:
        log_and_print(
            40,
            f"Failed to retrieve Slack access token. Please check your plugin configuration. Error: {e}",
        )
        return

    # Keeping local_user option for backwards compatibility with previous plugin version
    local_user = API(core).get_prism_slack_username()
    local_user_id = API(core).get_prism_slack_user_id()

    project = API(core).get_current_project()
    channel = get_channel_id(access_token, project)
    channel_users = get_channel_users(access_token, channel)
    slack_recipient = API(core).get_slack_user_id(notify_user, channel_users)

    slack_sender = (
        local_user_id if local_user_id else API(core).get_slack_user_id(local_user, channel_users)
    )

    _notify_slack_user(core, access_token, slack_recipient, channel, product, slack_sender)


# Notify user about new version of product is on the way!
def _notify_slack_user(
    core: object,
    access_token: str,
    slack_recipient: str,
    channel: str,
    product: str,
    slack_sender: str,
):
    """
    Notify the slack user about new render is on the way

    Args:
        core (object): The core application object
        access_token (str): Slack access token
        slack_recipient (str): Slack user ID of the recipient
        channel (str): Slack channel ID
        product (str): Name of the product being rendered
        slack_sender (str): Slack user ID of the sender
    """
    seq = os.getenv("PRISM_SEQUENCE")
    shot = os.getenv("PRISM_SHOT")
    asset = os.getenv("PRISM_ASSET")

    if os.getenv("PRISM_ASSET") == "" or os.getenv("PRISM_ASSET") is None:
        message = API(core).get_render_message(
            slack_recipient, seq=seq, shot=shot, product=product, sender=slack_sender
        )
    else:
        message = API(core).get_render_message(
            slack_recipient, asset=asset, product=product, sender=slack_sender
        )

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
