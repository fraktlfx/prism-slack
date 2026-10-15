import os
import re
import glob
import requests
from pprint import pprint

from prism_slack.server.blocks import SlackBlocks


def upload_content(
    access_token: str, channel_id: str, file: str, slack_user: str, state_data: dict
):
    """
    Upload a file to Slack and complete the upload process.

    Args:
       access_token (str): The Slack access token.
       channel_id (str): The ID of the Slack channel to upload the file to.
       file (str): The file path to be uploaded.
       slack_user (str): The Slack user ID of the uploader.
       state_data (dict): Additional state data for the upload.
    """

    # Resolve sequence templates (e.g. ####, %04d, $F4) to a concrete frame file for upload.
    upload_file = _resolve_upload_file(file, state_data.get("start_frame"))

    # Get the file size required for the upload
    file_size = os.stat(upload_file).st_size

    headers = {"Authorization": f"Bearer {access_token}"}
    url_request = "https://slack.com/api/files.getUploadURLExternal"
    payload = {"filename": upload_file, "length": file_size}

    try:
        # Get Slack to provide the URL used for the uploaded file
        response = requests.get(url_request, headers=headers, params=payload)
        response.raise_for_status()
        upload_data = response.json()
    except Exception as e:
        print(f"Error getting upload URL: {e}")
        return None

    # Store the URL and ID for the uploaded file
    upload_url = upload_data.get("upload_url")
    file_id = upload_data.get("file_id")

    try:
        # Upload the file to Slack
        with open(upload_file, "rb") as f:
            files = {"file": f}
            upload_response = requests.post(upload_url, headers=headers, files=files)
            upload_response.raise_for_status()
    except Exception as e:
        print(f"Error uploading the file: {e}")
        return None

    # Complete the upload process required by Slack
    post_url = "https://slack.com/api/files.completeUploadExternal"

    blocks = []

    tag_artist = state_data.get("tag_artist", False)

    comment_block = SlackBlocks.comments(
        slack_user,
        state_data.get("comments", ""),
        tag_artist=tag_artist,
    )
    if comment_block is not None:
        blocks.append(comment_block)

    if state_data.get("status") == "Request Review":
        blocks.append(SlackBlocks.divider())
        blocks.append(SlackBlocks.approval_buttons())

    post_payload = {
        "files": [{"id": file_id, "title": upload_file}],
        "channel_id": channel_id,
    }

    # If blocks exist, add them to the payload
    if blocks:
        post_payload["blocks"] = blocks

    try:
        response = requests.post(post_url, headers=headers, json=post_payload)
        response.raise_for_status()
        data = response.json()

        return data

    except Exception as e:
        print(f"Error completing Slack upload: {e}")
        return None


def _resolve_upload_file(file_path: str, start_frame: str | None = None) -> str:
    normalized = file_path.replace("\\", "/")

    if os.path.exists(normalized):
        return normalized

    if not re.search(r"#+|%0\d+d|\$F4", normalized):
        return normalized

    if start_frame is not None:
        frame_text = str(start_frame)
        candidate = normalized
        candidate = re.sub(
            r"%0(\d+)d", lambda m: frame_text.zfill(int(m.group(1))), candidate
        )
        candidate = re.sub(
            r"#+", lambda m: frame_text.zfill(len(m.group(0))), candidate
        )
        candidate = candidate.replace("$F4", frame_text.zfill(4))
        if os.path.exists(candidate):
            return candidate

    glob_pattern = re.sub(r"#+", "*", normalized)
    glob_pattern = re.sub(r"%0\d+d", "*", glob_pattern)
    glob_pattern = glob_pattern.replace("$F4", "*")
    matches = sorted(glob.glob(glob_pattern))
    if matches:
        return matches[0].replace("\\", "/")

    return normalized


def post_threaded_message(
    access_token: str, channel: str, message: str, thread_ts: str
):
    """
    Post a message to a thread in a Slack channel.

    Args:
       access_token (str): The Slack access token.
       channel (str): The ID of the Slack channel.
       message (str): The message text to post.
       thread_ts (str): The timestamp of the thread to post the message in.
    """

    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"channel": channel, "text": message, "thread_ts": thread_ts}
    try:
        requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print(f"Error posting threaded message: {e}")


def post_channel_message(access_token: str, channel: str, message: str):
    """
    Post a message to a Slack channel.

    Args:
        access_token (str): The Slack access token.
        channel (str): The ID of the Slack channel.
        message (str): The message text to post.
    """

    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"channel": channel, "text": message}
    try:
        requests.post(url, headers=headers, json=payload)

    except Exception as e:
        print(f"Error posting message: {e}")


def post_direct_message(access_token: str, slack_recipient: str, message: str):
    """
    Post a direct message to a Slack user.

    Args:
        access_token (str): The Slack access token.
        slack_recipient (str): The Slack user ID of the recipient.
        message (str): The message text to send.
    """

    url = "https://slack.com/api/conversations.open"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"users": slack_recipient}
    try:
        response = requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print(f"Error opening conversation: {e}")
        return

    post_url = "https://slack.com/api/chat.postMessage"
    payload = {"channel": response.json()["channel"].get("id"), "text": message}
    try:
        response = requests.post(post_url, headers=headers, json=payload)
    except Exception as e:
        print(f"Error sending direct message: {e}")


def post_channel_ephemeral_message(
    access_token: str, slack_recipient: str, channel_id: str, message: str
):
    """
    Post an ephemeral message to a Slack channel.

    Args:
        access_token (str): The Slack access token.
        slack_recipient (str): The Slack user ID of the recipient.
        channel_id (str): The ID of the Slack channel.
        message (str): The message text to send.
    """

    url = "https://slack.com/api/chat.postEphemeral"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"channel": channel_id, "user": slack_recipient, "text": message}

    requests.post(url, headers=headers, json=payload)


def post_direct_ephemeral_message(
    access_token: str, slack_recipient: str, message: str
):
    """
    Post an ephemeral direct message to a Slack user.

    Args:
        access_token (str): The Slack access token.
        slack_recipient (str): The Slack user ID of the recipient.
        message (str): The message text to send.
    """

    url = "https://slack.com/api/conversations.open"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"users": slack_recipient}
    try:
        response = requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print(f"Error opening conversation: {e}")
        return

    post_url = "https://slack.com/api/chat.postEphemeral"
    payload = {
        "channel": response.json()["channel"].get("id"),
        "user": slack_recipient,
        "text": message,
    }
    try:
        response = requests.post(post_url, headers=headers, json=payload)
    except Exception as e:
        print(f"Error sending direct message: {e}")


def post_update_message(
    access_token: str,
    channel_id: str,
    message_text: str,
    timestamp: str,
    metadata,
    blocks=None,
):
    """
    Update a Slack message with additional metadata based on the version information.

    Args:
        access_token (str): The Slack access token.
        channel_id (str): The ID of the Slack channel.
        message_text (str): The text of the message to update.
        timestamp (str): The timestamp of the message to update.
        metadata (Dict[str, str]): The metadata to attach to the message.
        blocks (optional): The blocks to include in the message.
    """
    url = "https://slack.com/api/chat.update"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json;",
    }
    payload = {
        "channel": channel_id,
        "ts": timestamp,
        "metadata": {"event_type": "prism_publish", "event_payload": metadata},
    }
    if message_text is not None:
        payload["text"] = message_text

    if blocks is not None:
        payload["blocks"] = blocks
    pprint(f"Payload:{payload}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        return data

    except Exception as e:
        print(f"Error updating the chosen messge: {e}")


def post_signout_slack(user_access_token: str):
    """
    Revoke the Slack access token to sign the user out.

    Args:
        user_access_token (str): The Slack access token to revoke.
    """

    url = "https://slack.com/api/auth.revoke"
    headers = {"Authorization": f"Bearer {user_access_token}"}
    payload = {"token": user_access_token}

    try:
        requests.post(url, headers=headers, json=payload)

    except Exception as e:
        print(f"Error signing out of Slack: {e}")
