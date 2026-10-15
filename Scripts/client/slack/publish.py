import os
import time
import json
from typing import Any

from prism_slack.client.prism.api import API
from prism_slack.client.prism.ui import SuccessfulPOST, UploadDialog
from ..prism.utils.logging import log_and_print
from ..prism.utils.convert_image_sequence import check_conversion

from prism_slack.client.slack.slack_config import SlackConfig
from .api.get import get_channel_history, get_channel_id
from .api.post import post_update_message, upload_content

from qtpy.QtCore import QTimer


class Publish:
    def __init__(self, core: object):
        self.core = core

    def publish_to_slack(self, file: str, state_data: dict):
        """
        Publish the given file to Slack based on the provided state data.

        Args:
            file (str): The file path to be published.
            state_data (dict): The state data containing settings from the state manager.
        """
        log_and_print(10, f"Preparing to publish to Slack: {file}")

        # -----------
        # Determine if the file is being published from the Media Browser or the Execution Graph and check if conversion is needed based on the file extension and user settings.
        # If the file is being published from the Media Browser, skip the conversion check and publish the file directly, as the Media Browser publish should already handle conversion settings.
        # -----------
        if state_data["ui"] != "Media" and state_data["ui"] != "EG":
            log_and_print(
                10,
                f"[Slack] Publishing file from non-Media Browser/Execution Graph UI: {file}",
            )

            ext = os.path.splitext(file)[1].replace(".", "")
            upload = check_conversion(self.core, state_data, ext, file)[0]
            log_and_print(
                10,
                f"[Slack] File after conversion check: {upload}",
            )
        else:
            upload = file
            log_and_print(
                10,
                f"Publishing file from Media Browser: {upload}",
            )

        # -----------
        # Retrieve the Slack access token from the Prism API and log it for debugging purposes.
        # -----------
        try:
            log_and_print(10, "[Slack] Retrieving Slack access token")
            access_token = API(self.core).get_access_token()

        except Exception as e:
            log_and_print(
                40,
                f"Failed to retrieve Slack access token. Please check your configuration.\n\n{e}",
            )

        # -----------
        # Ensure the file path uses forward slashes, and log the final upload path for debugging purposes.
        # -----------
        try:
            upload = upload.replace("\\", "/")
            log_and_print(
                10,
                f"[Slack] Final upload path after replacing backslashes: {upload}",
            )
        except AttributeError:
            log_and_print(
                30,
                f"Upload path is not a string, cannot replace backslashes: {upload}. Passing... ",
            )
            pass

        # -----------
        # If you are not publishing from a Deadline job, use a single shot timer to delay the upload to ensure that the publish process has completed
        # and the file is fully written before attempting to upload to Slack.
        #
        # If you are publishing from the Deadline Monitor, skip the timer and upload immediately to avoid issues with the Deadline Monitor's handling of timers and threads.
        # -----------
        if state_data["ui"] != "DL" and state_data["ui"] != "EG":
            log_and_print(
                10,
                "[Slack] Publishing from non-Deadline UI, using QTimer to delay upload.",
            )
            QTimer.singleShot(
                0,
                lambda: self.upload_to_slack(
                    access_token=access_token,
                    file=upload,
                    state_data=state_data,
                ),
            )

        else:
            log_and_print(10, "[Slack] Publishing from a Deadline job.")
            self.upload_to_slack(
                access_token=access_token,
                file=upload,
                state_data=state_data,
            )

    # Upload file to Slack
    def upload_to_slack(self, access_token: str, file: str, state_data: dict):
        """
        Upload the file to Slack and update the message with metadata.
        Args:
            access_token (str): The Slack access token.
            file (str): The file path to be uploaded.
            state_data (dict): The state data containing settings from the state manager/media browser.
        """
        # -----------
        # If the file is being published from the Media Browser, prompt the upload dialog.
        # -----------
        if state_data["ui"] == "Media":
            upload_dialog = UploadDialog()
            upload_dialog.show()

        # -----------
        # Get the current project name, Slack channel ID, and Slack User
        # -----------
        current_project = f"{state_data['project']}"
        channel_id = get_channel_id(access_token, current_project)
        # channel_users = slack.get_channel_users(access_token, channel_id)
        if state_data["ui"] == "DL":
            slack_user = state_data.get("user")
        else:
            slack_user = API(self.core).get_prism_slack_user_id()

        # -----------
        # Determine if the plugin needs to tag the artist
        # -----------
        state_data["tag_artist"] = API(self.core).get_tag_artist()

        # -----------
        # Log the collected information for debugging purposes.
        # -----------
        log_and_print(10, f"File: {file}")
        log_and_print(10, f"State Data: {state_data}")
        log_and_print(10, f"Channel ID: {channel_id}")
        log_and_print(10, f"Slack User ID: {slack_user}")

        upload_result = None
        try:
            # -----------
            # Attempt to upload the file to Slack
            # -----------
            upload_result = upload_content(
                access_token=access_token,
                channel_id=channel_id,
                file=file,
                slack_user=slack_user,
                state_data=state_data,
            )
        except Exception as e:
            log_and_print(40, f"Failed to upload file to Slack: {e}")

        # -----------
        # If the upload failed, prompt the user that it failed and exit the function.
        # Otherwise if it succeeded, and the publish is from the Media Browser, close the upload dialog and prompt that it was successful.
        # -----------
        if not upload_result:
            if state_data["ui"] == "Media":
                SuccessfulPOST(False, state_data["ui"])
            log_and_print(40, "File upload to Slack failed, no response received.")
            return

        uploaded = True
        if state_data["ui"] == "Media":
            upload_dialog.close()
            SuccessfulPOST(uploaded, state_data["ui"])
            log_and_print(10, "File uploaded to Slack successfully.")

        # -----------
        # Get the versioninfo file and convert the path to use forward slashes for consistency
        # -----------
        versioninfo = state_data.get("versioninfo")
        try:
            versioninfo = versioninfo.as_posix()
        except AttributeError:
            pass

        # -----------
        # Construct the metadata to be added to the Slack message, including the published user, versioninfo path, and status if server approvals are enabled.
        # -----------
        metadata = {
            "published_user": slack_user,
            "versioninfo": versioninfo,
        }

        status = state_data.get("status")
        if status and API(self.core).get_server_approvals():
            metadata["status"] = status

        # -----------
        # If there is custom metadata in the state data, merge it with the existing metadata to be added to the Slack message.
        # -----------
        custom_metadata = state_data.get("metadata_payload")
        if isinstance(custom_metadata, dict):
            metadata.update(custom_metadata)

        log_and_print(10, f"Constructed metadata for Slack message: {metadata}")

        # -----------
        # Grab the file ID from the upload response and use it to find the timestamp of the message containing the uploaded file by checking the channel history.
        # Then use the timestamp to update the message with the constructed metadata.
        # -----------
        files = (upload_result or {}).get("files") or []
        if not files:
            log_and_print(40, "Slack upload response did not include file metadata.")
            return

        file_id = files[0].get("id")

        timeout = 20
        timestamp = None

        # -----------
        # Check the channel history for the last 30 messages to find the message containing the uploaded file and retrieve its timestamp.
        # If the message is not found immediately, keep checking every 2 seconds until it is found or until the timeout is reached.
        # -----------
        while True:
            msg_history = get_channel_history(
                access_token=access_token, channel_id=channel_id, message_limit=30
            )
            timestamp = self._get_timestamp(file_id, msg_history)

            if timestamp is not None:
                log_and_print(
                    10,
                    f"Found message containing uploaded file with timestamp: {timestamp}",
                )
                break

            timeout -= 1
            log_and_print(
                10,
                f"Message containing uploaded file not found yet, retrying... Timeout in {timeout} seconds.",
            )
            time.sleep(2)

        if timeout <= 0:
            log_and_print(40, "Timed out waiting for message timestamp.")
            return

        # -----------
        # Grab the existing message text and blocks to include in the update, then call the function to update the message with the new metadata.
        # -----------
        message_text = self._get_message_text(msg_history, timestamp)
        message_blocks = self._get_message_blocks(msg_history, timestamp)

        log_and_print(
            10,
            f"Retrieved message text and blocks for update: {{'text': {message_text}, 'blocks': {message_blocks}}}",
        )
        log_and_print(
            10,
            f"Updating Slack message with new metadata for file: {file}",
        )

        try:
            _ = post_update_message(
                access_token=access_token,
                channel_id=channel_id,
                timestamp=timestamp,
                message_text=message_text,
                blocks=message_blocks,
                metadata=metadata,
            )
            log_and_print(10, "Slack message updated successfully with new metadata.")
        except Exception as e:
            log_and_print(40, f"Failed to update Slack message: {str(e)}")

        # After updating the message, check to make sure that the necessary statuses are included in the project settings
        # -----------
        self._check_statuses_in_project_config()

        # -----------
        # Finally, apply the Slack information to the versioninfo file for the published version.
        # -----------
        self._apply_info_to_versioninfo(state_data=state_data, ts=timestamp)

    def _get_timestamp(self, file_id: str, messages: list[dict[str, Any]]):
        """
        Retrieve the timestamp of the message containing the uploaded file.

        Args:
            file_id (str): The ID of the uploaded file.
            messages (list[dict[str, Any]]): The list of messages from the channel history.

        Returns:
            str: The timestamp of the message containing the file, or an empty string if not found.
        """

        for msg in messages or []:
            for m in msg.get("files") or []:
                if m.get("id") == file_id:
                    timestamp = msg.get("ts")
                    return timestamp

        return ""

    def _get_message_text(self, messages: list[dict[str, Any]], timestamp: str):
        """
        Retrieve the text of the message containing the uploaded file.

        Args:
            messages (list[dict[str, Any]]): The list of messages from the channel history.
            timestamp (str): The timestamp of the message to retrieve text for.

        Returns:
            str: The text of the message containing the file, or an empty string if not found.
        """

        for msg in messages or []:
            if msg.get("ts") == timestamp:
                return msg.get("text", " ") or " "
        return " "

    def _get_message_blocks(self, messages: list[dict[str, Any]], timestamp: str):
        """
        Retrieve the blocks of the message containing the uploaded file.
        **-----THE EMPTY STRING IS REQUIRED FOR SLACK TO ACCEPT NO BLOCKS-----**

        Args:
            messages (list[dict[str, Any]]): The list of messages from the channel history.
            timestamp (str): The timestamp of the message to retrieve blocks for.

        Returns:
            list[dict[str, Any]] | str: The blocks of the message containing the file, or an empty string if not found.
        """

        for msg in messages or []:
            if msg.get("ts") == timestamp:
                blocks = msg.get("blocks")
                return blocks if blocks else ""
        return ""

    def _apply_info_to_versioninfo(self, state_data: dict, ts: str):
        """
        Apply Slack post information to the versioninfo file for the published version

        Args:
            state_data (dict): The state data containing the necessary information to publish the content to Slack, including the versioninfo file, status, ui, project name, etc.
            ts (str): The timestamp for the selected message on Slack
        """
        log_and_print(
            10,
            f"Applying Slack information to versioninfo file with state data: {state_data} and timestamp: {ts}",
        )
        with open(state_data["versioninfo"], "r", encoding="utf-8") as f:
            versioninfo: dict = json.load(f)

        # Add slack timestamp to versioninfo file
        if "slack" not in versioninfo:
            versioninfo["slack"] = {}
            versioninfo["slack"]["ts"] = ts
            log_and_print(10, "Applied Slack timestamp to versioninfo")

        # If the Project Management plugin is enabled and the project manager is Prism, update the version status based on the Slack status
        if (
            self.core.getPlugin("ProjectManagement")
            and API(self.core).get_project_manager() == "Prism"
            and API(self.core).get_approvals_update_status()
        ):
            if state_data.get("status") == "Request Review":
                versioninfo["status"] = "rev"
            else:
                versioninfo["status"] = "ip"
        else:
            log_and_print(
                10,
                "Project Management plugin is not enabled or project manager is not Prism, skipping status update in versioninfo.",
            )

        with open(state_data["versioninfo"], "w") as f:
            json.dump(versioninfo, f, indent=4)
            log_and_print(
                10, "Successfully applied Slack information to versioninfo file."
            )

        return

    def _check_statuses_in_project_config(self):
        cbb_status = {
            "name": "Could Be Better",
            "abbreviation": "cbb",
            "icon": "",
            "color": [85, 85, 127],
            "tasks": False,
            "products": True,
            "media": True,
        }
        att_status = {
            "name": "Needs Revised",
            "abbreviation": "att",
            "icon": "",
            "color": [170, 0, 0],
            "tasks": False,
            "products": True,
            "media": True,
        }
        if (
            self.core.getPlugin("ProjectManagement")
            and API(self.core).get_project_manager() == "Prism"
        ):
            status_list = API(self.core).get_media_status_list()
            status_abb_list = []
            for sl in status_list:
                status_abb_list.append(sl.get("abbreviation"))

            if "cbb" not in status_abb_list or "att" not in status_abb_list:
                project_config = SlackConfig(self.core).load_config(mode="project")
                prism_statuses = project_config["prjManagement"].get("prism_status", [])

                if "cbb" not in status_abb_list:
                    prism_statuses.append(cbb_status)
                    log_and_print(
                        10, "Added 'Could Be Better' status to prism_statuses"
                    )

                if "att" not in status_abb_list:
                    prism_statuses.append(att_status)
                    log_and_print(10, "Added 'Needs Revised' status to prism_statuses")

                project_config["prjManagement"]["prism_status"] = prism_statuses
                SlackConfig(self.core).save_config_setting(
                    project_config, mode="project"
                )
        else:
            log_and_print(
                10,
                "Project Management plugin is not enabled or project manager is not Prism, skipping status check and update in project config.",
            )
            return
