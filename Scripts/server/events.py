import time
import json
import requests
from pprint import pprint

from prism_slack.client.prism.api import API
from prism_slack.client.slack.api.get import (
    get_usergroup_users,
    get_usergroups,
    get_user_info,
    get_channel_history,
)
from prism_slack.client.slack.api.post import post_threaded_message
from prism_slack.server.blocks import SlackBlocks as sb


class SlackEvents:
    def __init__(self, app, token, core):
        self.core = core
        self.app = app
        self.token = token
        self.metadata = {}

        # ------------------------------
        # REMEMBER, YOU CAN USE PCORE IN HERE TO ACCESS THE CORE FUNCTIONALITY TO FURTHER ENHANCE YOUR SLACK APP
        # ------------------------------

        # Register actions
        self.register_actions()

    def _verify_user_in_usergroup(self, user_id):
        usergroup = API(self.core).get_approvals_usergroup()
        usergroup_list = get_usergroups(self.token)
        for ug in usergroup_list:
            if ug["name"] == usergroup:
                usergroup_id = ug["id"]
                break

        users = get_usergroup_users(self.token, usergroup_id)
        if user_id in users:
            return True
        return False

    def _acquire_metadata_from_message(self, body):
        return {
            "timestamp": body["message"]["ts"],
            "channel": body["channel"]["id"],
            "artist": body.get("message")
            .get("metadata")
            .get("event_payload")
            .get("published_user"),
            "reviewer": body["user"]["id"],
            "versioninfo": body["message"]["metadata"]["event_payload"].get(
                "versioninfo"
            ),
        }

    def _acquire_slack_display_name(self, user_id):
        user_info = get_user_info(self.token, user_id)
        display_name = user_info["profile"].get("display_name") or user_info[
            "profile"
        ].get("real_name")
        return display_name

    def _apply_to_versioninfo(self, versioninfo_path, status, note):
        with open(versioninfo_path, "r") as f:
            version_data = json.load(f)

        if status is None:
            pass
        elif "status" in version_data:
            version_data["status"] = status
        else:
            version_data["status"] = status

        if "notes" in version_data:
            version_data["notes"].append(note)
        else:
            version_data["notes"] = [note]

        with open(versioninfo_path, "w") as f:
            json.dump(version_data, f, indent=4)

    def register_actions(self):
        # Register the event handler for when a channel is created
        @self.app.event("channel_created")
        def event_channel_created(ack, event, say):
            ack()
            channel_id = event["channel"]["id"]

            url = "https://slack.com/api/conversations.join"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            payload = {"channel": channel_id}

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                if response.json().get("ok"):
                    print(f"Joined channel: {channel_id}")
                else:
                    print(
                        f"Failed to join channel: {channel_id}\n\n {response.json().get('error')}"
                    )
            else:
                print(f"Failed to join channel: {channel_id}\n\n {response.text}")

        @self.app.action("button_approved")
        def action_button_approved(body, ack, say):
            ack()

            channel = body["channel"]["id"]
            thread_ts = body["message"].get("ts")
            comment_text = f"Marked as: Approved by <@{body['user']['id']}>"
            approver_display_name = self._acquire_slack_display_name(body["user"]["id"])

            versioninfo_path = body["message"]["metadata"]["event_payload"].get(
                "versioninfo"
            )
            if not versioninfo_path:
                self.app.logger.warning(
                    "Missing versioninfo in message metadata. "
                    "Likely due to having been published from a Slack plugin older than 2.1.1.\nCurrent Posts Event Payload=%s",
                    body["message"]["metadata"]["event_payload"],
                )
                versioninfo_path = None

            note = {
                "date": time.time(),
                "author": approver_display_name,
                "content": "Marked as: Approved",
                "replies": [],
                "id": thread_ts,
            }

            # If the Approvals Usergroup feature is enabled, check if the user is in the usergroup before allowing them to Approve the version. If the feature is not enabled, allow anyone to Approve.
            if API(self.core).get_approvals_usergroup_status():
                # If the user is in the approvals usergroup, post the message and update the versioninfo with the CBB status. If not, open the Invalid User Modal window
                if self._verify_user_in_usergroup(body["user"]["id"]):
                    post_threaded_message(self.token, channel, comment_text, thread_ts)
                    if versioninfo_path is not None:
                        self._apply_to_versioninfo(
                            versioninfo_path=versioninfo_path, status="apr", note=note
                        )
                else:
                    _view_submission_invalid_user(
                        ack, body=body, client=self.app.client
                    )
            else:
                post_threaded_message(self.token, channel, comment_text, thread_ts)
                if versioninfo_path is not None:
                    self._apply_to_versioninfo(
                        versioninfo_path=versioninfo_path, status="apr", note=note
                    )

        # When the Needs Revised Button is clicked, gather information and open the Modal window
        @self.app.action("button_needs_revised")
        def action_button_needs_revised(body, ack, client):
            ack()
            artist = (
                body.get("message")
                .get("metadata")
                .get("event_payload")
                .get("published_user")
            )
            metadata = json.dumps(self._acquire_metadata_from_message(body))

            # If the Approvals Usergroup feature is enabled, check if the user is in the usergroup before allowing them to post Needs Revised feedback. If the feature is not enabled, allow anyone to submit Needs Revised feedback.
            if API(self.core).get_approvals_usergroup_status():
                # If the user is in the approvals usergroup, post the message and update the versioninfo with the CBB status. If not, open the Invalid User Modal window
                if self._verify_user_in_usergroup(body["user"]["id"]):
                    pass  # Allow user to open the Needs Revised modal
                else:
                    _view_submission_invalid_user(
                        ack, body=body, client=self.app.client
                    )
                    return
            else:
                pass

            client.views_open(
                trigger_id=body["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "modal-needs-revised",
                    "title": {"type": "plain_text", "text": "Needs Revised"},
                    "blocks": [
                        sb.revision_description(artist),
                        sb.text_input(),
                    ],
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "submit": {"type": "plain_text", "text": "Submit"},
                    "private_metadata": metadata,
                },
            )

        # When the Needs Revised Submit Button is clicked, close the Modal window and make a Threaded response
        @self.app.view("modal-needs-revised")
        def view_submission_needs_revised(ack, body, client):
            ack()

            metadata = json.loads(body["view"]["private_metadata"])
            reviewer = metadata["reviewer"]
            artist = metadata["artist"]
            channel = metadata["channel"]
            thread_ts = metadata["timestamp"]

            for block in body["view"]["blocks"]:
                if "element" in block and "action_id" in block["element"]:
                    element_id = block["element"]["action_id"]
                    break
            comments = body["view"]["state"]["values"]["input_comments"][element_id][
                "value"
            ]
            text = f"*Status:* *Needs Revised*\n*Artist*: <@{artist}> \n*Reviewer:* <@{reviewer}>\n\n*Comments:* {comments}"

            versioninfo_path = metadata.get("versioninfo")
            if not versioninfo_path:
                self.app.logger.warning(
                    "Missing versioninfo in message metadata. "
                    "Likely due to having been published from a Slack plugin older than 2.1.1.\nCurrent Posts Event Payload=%s",
                    body["message"]["metadata"]["event_payload"],
                )
                versioninfo_path = None

            note = {
                "date": time.time(),
                "author": self._acquire_slack_display_name(reviewer),
                "content": f"{comments}",
                "replies": [],
                "id": thread_ts,
            }

            post_threaded_message(self.token, channel, text, thread_ts)

            # If the Approvals Usergroup feature is enabled, check if the user is in the usergroup before allowing them to post Needs Revised feedback. If the feature is not enabled, allow anyone to submit Needs Revised feedback.
            if versioninfo_path is not None:
                self._apply_to_versioninfo(
                    versioninfo_path=versioninfo_path, status="att", note=note
                )

        # When the CBB Button is clicked, gather information and open the Modal window
        @self.app.action("button_cbb")
        def action_button_cbb(body, ack, client):
            ack()
            artist = (
                body.get("message")
                .get("metadata")
                .get("event_payload")
                .get("published_user")
            )
            metadata = json.dumps(self._acquire_metadata_from_message(body))

            # If the Approvals Usergroup feature is enabled, check if the user is in the usergroup before allowing them to post Needs Revised feedback. If the feature is not enabled, allow anyone to submit Needs Revised feedback.
            if API(self.core).get_approvals_usergroup_status():
                # If the user is in the approvals usergroup, post the message and update the versioninfo with the CBB status. If not, open the Invalid User Modal window
                if self._verify_user_in_usergroup(body["user"]["id"]):
                    pass  # Allow user to open the Needs Revised modal
                else:
                    _view_submission_invalid_user(
                        ack, body=body, client=self.app.client
                    )
                    return
            else:
                pass

            client.views_open(
                trigger_id=body["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "modal-cbb",
                    "title": {"type": "plain_text", "text": "Could Be Better"},
                    "blocks": [
                        sb.cbb_description(artist),
                        sb.text_input(),
                    ],
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "submit": {"type": "plain_text", "text": "Submit"},
                    "private_metadata": metadata,
                },
            )

        # When the CBB Submit Button is clicked, close the Modal window and make a Threaded response
        @self.app.view("modal-cbb")
        def view_submission_cbb(ack, body, client):
            ack()

            metadata = json.loads(body["view"]["private_metadata"])
            reviewer = metadata["reviewer"]
            artist = metadata["artist"]
            channel = metadata["channel"]
            thread_ts = metadata["timestamp"]

            for block in body["view"]["blocks"]:
                if "element" in block and "action_id" in block["element"]:
                    element_id = block["element"]["action_id"]
                    break
            comments = body["view"]["state"]["values"]["input_comments"][element_id][
                "value"
            ]
            text = f"*Status:* *CBB*\n*Artist*: <@{artist}> \n*Reviewer:* <@{reviewer}>\n\n*Comments:* {comments}"

            versioninfo_path = metadata.get("versioninfo")
            if not versioninfo_path:
                self.app.logger.warning(
                    "Missing versioninfo in message metadata. "
                    "Likely due to having been published from a Slack plugin older than 2.1.1.\nCurrent Posts Event Payload=%s",
                    body["message"]["metadata"]["event_payload"],
                )
                versioninfo_path = None

            note = {
                "date": time.time(),
                "author": self._acquire_slack_display_name(reviewer),
                "content": f"{comments}",
                "replies": [],
                "id": thread_ts,
            }

            post_threaded_message(self.token, channel, text, thread_ts)
            # If the Approvals Usergroup feature is enabled, check if the user is in the usergroup before allowing them to post Needs Revised feedback. If the feature is not enabled, allow anyone to submit Needs Revised feedback.
            if versioninfo_path is not None:
                self._apply_to_versioninfo(
                    versioninfo_path=versioninfo_path, status="cbb", note=note
                )

        # When the Invalid User Modal is triggered, open the Modal window
        @self.app.view("modal-invalid-user")
        def _view_submission_invalid_user(ack, body, client):
            ack()

            client.views_open(
                trigger_id=body["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "modal-invalid-user",
                    "title": {"type": "plain_text", "text": "Invalid User"},
                    "blocks": [
                        sb.invalid_user_description(),
                    ],
                    "close": {"type": "plain_text", "text": "Close"},
                },
            )

        @self.app.event("message")
        def _event_message(body, logger):
            event = body.get("event", {})

            # Grab the parent message's timestamp and channel ID
            parent_ts = event.get("thread_ts")
            channel_id = event.get("channel")

            # Grab the parent message from the channels history
            parent_message = get_channel_history(
                self.token,
                channel_id,
                message_limit=1,
                oldest=parent_ts,
                inclusive=True,
            )[0]
            try:
                # Check if the parent message has "prism_publish" event type and if so, extract the versioninfo path from the metadata
                parent_metadata = parent_message.get("metadata", {})
                if parent_metadata.get("event_type") == "prism_publish":
                    versioninfo_path = parent_metadata.get("event_payload").get(
                        "versioninfo"
                    )
                    thread_ts = event.get("ts")
                    user_id = event.get("user")
                    text = event.get("text")

                    # If the message mentions one or more users, replace the user IDs with their display names in the text
                    while "<@" in text:
                        mentioned_user_id = text.split("<@")[1].split(">")[0]
                        mentioned_user_name = self._acquire_slack_display_name(
                            mentioned_user_id
                        )

                        # Replace the user ID with the display name in the text
                        text = text.replace(
                            f"<@{mentioned_user_id}>", f"{mentioned_user_name}"
                        )

                    note = {
                        "date": time.time(),
                        "author": self._acquire_slack_display_name(user_id),
                        "content": text,
                        "replies": [],
                        "id": thread_ts,
                    }

                    self._apply_to_versioninfo(versioninfo_path, status=None, note=note)

            except Exception as e:
                pprint(f"Error accessing parent message metadata: {e}")
                parent_metadata = {}
