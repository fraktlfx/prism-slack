import requests


# Get the users information
def get_user_info(access_token: str, user_id: str):
    url = "https://slack.com/api/users.info"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"user": user_id}

    try:
        response = requests.get(url, headers=headers, params=payload)
        user_info = response.json()["user"]

    except Exception as e:
        print(f"Error getting user info: {e}")
        return

    return user_info


# Get Slack Channel ID from conversation list
def get_channel_id(access_token: str, project_name: str):
    conversation_id = None
    url = "https://slack.com/api/conversations.list"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": 1000, "types": "public_channel,private_channel"}
    page = None

    try:
        while True:
            if page:
                params["cursor"] = page

            response = requests.get(url, headers=headers, params=params)

            conversations = response.json()

            for conversation in conversations["channels"]:
                if conversation["name"] == project_name:
                    conversation_id = conversation["id"]
                    return conversation_id

            page = conversations.get("response_metadata", {}).get("next_cursor")
            if not page:
                break

    except Exception as e:
        print(f"Error getting channel ID: {e}")
        return None


# Get the Users in a Slack Channel, saving only their display name and id
def get_channel_users(access_token: str, channel_id: str):
    url = "https://slack.com/api/conversations.members"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"channel": channel_id}

    response = requests.get(url, headers=headers, params=params)

    channel_members = response.json()["members"]
    channel_users = []

    for m in channel_members:
        url = "https://slack.com/api/users.info"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"user": m}

        response = requests.get(url, headers=headers, params=params)

        user = response.json().get("user")

        try:
            user_name = user["profile"].get("display_name")
        except Exception:
            user_name = user["profile"].get("real_name")

        user_id = user.get("id")

        if user.get("is_bot") is False:
            channel_users.append({"id": user_id, "display_name": user_name})

    return channel_users


def get_file_timestamp(access_token: str, channel_id: str, file_id: str):
    """
    Get the timestamp of the uploaded file in Slack.

    Args:
        access_token (str): The Slack access token.
        channel_id (str): The ID of the Slack channel.
        file_id (str): The ID of the uploaded file.

    Returns:
        timestamp (str): The timestamp of the uploaded file.
    """

    url = "https://slack.com/api/files.info"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"file": file_id}

    response = requests.get(url, headers=headers, params=params)

    file_info = response.json().get("file")

    timestamp = file_info.get("timestamp")

    return timestamp


def get_channel_history(
    access_token: str,
    channel_id: str,
    message_limit: int = 30,
    oldest: str = None,
    inclusive: bool = True,
):
    """
    Get the message history of a Slack channel. Limited to the last 30 messages.

    Args:
        access_token (str): The Slack access token.
        channel_id (str): The ID of the Slack channel.
        message_limit (int) (Optional): The maximum number of messages to retrieve.
        oldest (str) (Optional): The timestamp of the oldest message to include in the results.
        inclusive (bool) (Optional): Whether to include the message with the timestamp equal to oldest.

    Returns:
        messages (list): The list of messages in the channel.
    """

    url = "https://slack.com/api/conversations.history"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "channel": channel_id,
        "limit": message_limit,
        "include_all_metadata": True,
    }

    if oldest is not None:
        params["oldest"] = oldest
    if inclusive is not None:
        params["inclusive"] = inclusive

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error getting channel history: {response.text}")
        return []

    messages = response.json().get("messages", [])

    return messages


def get_permalink(access_token: str, channel_id: str, ts: str):
    """
    Get the permalink for the published message to send user to post

    Args:
        access_token (str): The Slack bot access token
        channel_id (str): The Slack Channel ID for the project
        ts (str): The message timestamp derived from the versioninfo file

    Return:
        permalink (str): The permalink that the user will be sent towards
    """
    url = "https://slack.com/api/chat.getPermalink"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"channel": channel_id, "message_ts": ts}

    response = requests.get(url, headers=headers, params=params)

    permalink = response.json().get("permalink")

    return permalink


def get_studio_users(core):
    studio = core.getPlugin("Studio")
    data = studio.getStudioUsers()
    users = []
    for user in data:
        if user.get("role") not in ["deactivated"]:
            users.append(user.get("name"))

    return users
