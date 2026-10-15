class SlackBlocks:
    """
    Class to define various Slack block structures for messages and modals.
    """

    def __init__(self):
        pass

    def identifier_information(
        sequence: str,
        shot: str,
        identifier: str,
        version: str,
        artist: str,
        user_avatar: str,
        status: str,
    ):
        """
        Return the block for identifier information. Not currently in use.

        Args:
            sequence (str): The sequence name.
            shot (str): The shot name.
            identifier (str): The identifier.
            version (str): The version of the product.
            artist (str): The artist's Slack user ID.
            user_avatar (str): The URL of the user's avatar image.
            status (str): The status of the submission.

        Returns:
            dict: A dictionary representing the Slack block for identifier information.
        """

        return {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Sequence:* _{sequence}_"},
                {"type": "mrkdwn", "text": f"*Identifier:* _{identifier}_"},
                {"type": "mrkdwn", "text": f"*Shot:* _{shot}_"},
                {"type": "mrkdwn", "text": f"*Version:* _{version}_"},
                {"type": "mrkdwn", "text": f"*Artist:* _<@{artist}>_"},
                {"type": "mrkdwn", "text": f"*Status:* _{status}_"},
            ],
            "accessory": {
                "type": "image",
                "image_url": user_avatar,
                "alt_text": "User profile picture",
            },
        }

    def product_information(asset: str, task: str, product: str, version: str, artist: str):
        """
        Return the block for product information.

        Args:
            asset (str): The asset name.
            task (str): The task name.
            product (str): The product name.
            version (str): The version of the product.
            artist (str): The artist's Slack user ID.

        Returns:
            dict: A dictionary representing the Slack block for product information.
        """

        return {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Asset: *\n{asset}"},
                {"type": "mrkdwn", "text": f"*Task: *\n{task}"},
                {"type": "mrkdwn", "text": f"*Product: *\n{product}"},
                {"type": "mrkdwn", "text": f"*Version: *\n{version}"},
                {"type": "mrkdwn", "text": f"*Artist: *\n{artist}"},
            ],
        }

    def comments(artist: str, comments: str, tag_artist: bool = False):
        """
        Return the comments block for submissions.

        Args:
            artist (str): The artist's Slack user ID.
            comments (str): The comments text.
            tag_artist (bool): Whether to tag the artist in the comments.

        Returns:
            dict: A dictionary representing the Slack block for comments.
        """

        artist = artist.strip() if artist else ""
        comments = comments.strip() if comments else ""

        text = []
        print(f"Tag Artist: {tag_artist}")
        if tag_artist is not False and artist:
            text.append(f"*Artist:* <@{artist}>")

        if comments:
            text.append(f"*Comments:* {comments}")

        if not text:
            return None

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(text),
            },
        }

    def revision_description(artist: str):
        """
        Return the revision description block for modal popups.

        Args:
            artist (str): The artist's Slack user ID.

        Returns:
            dict: A dictionary representing the Slack block for revision description.
        """

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Uh oh, looks like this needs some love. Leave some revision comments/notes for <@{artist}>.",
            },
        }

    def cbb_description(artist: str):
        """
        Return the CBB description block for modal popups.

        Args:
            artist (str): The artist's Slack user ID.

        Returns:
            dict: A dictionary representing the Slack block for CBB description.
        """

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Leave some comments/notes for <@{artist}> and let them know how this can be better, if time allows of course.",
            },
        }

    def invalid_user_description():
        """
        Return the invalid user description block for modal popups.

        Returns:
            dict: A dictionary representing the Slack block for invalid user description.
        """

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "You are not part of the approvals team. If this is incorrect, please contact your Slack Workspace Admin to be added to the correct Usergroup.",
            },
        }

    def text_input():
        """
        Return the text input block for modal popups.

        Returns:
            dict: A dictionary representing the Slack block for text input.
        """

        return {
            "type": "input",
            "block_id": "input_comments",
            "label": {"type": "plain_text", "text": "Comments"},
            "element": {"type": "plain_text_input", "multiline": True},
        }

    def approval_buttons():
        """
        Return the approval buttons block for publishing.

        Returns:
            dict: A dictionary representing the Slack block for approval buttons.
        """

        return {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "emoji": True, "text": "Approved"},
                    "style": "primary",
                    "action_id": "button_approved",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Needs Revised",
                    },
                    "style": "danger",
                    "action_id": "button_needs_revised",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "emoji": True, "text": "CBB"},
                    "action_id": "button_cbb",
                },
            ],
        }

    def divider():
        """
        Return the divider block.

        Returns:
            dict: A dictionary representing the Slack divider block.
        """

        return {"type": "divider"}
