import os
import time
import json
from typing import List, Dict, Any

from Scripts.client.prism.ui import UploadDialog, SuccessfulPOST
from Scripts.client.prism.api import API
from Scripts.client.slack.api import (
    get_channel_id,
    get_channel_users,
    get_channel_history,
    upload_content,
)
from Scripts.client.prism.utils.convert_image_sequence import (
    check_conversion,
    log_and_print,
)

from qtpy.QtCore import QTimer


class Publish:
    def __init__(self, core: object):
        self.core = core

    def publish_to_slack(self, file: str, state_data: dict, prism_user: str):
        if state_data["ui"] != "Media":
            log_and_print(
                20,
                f"Publishing file from non-Media Browser/Execution Graph UI: {file}",
            )

            ext = os.path.splitext(file)[1].replace(".", "")
            upload = check_conversion(self.core, state_data, ext, file)[0]
            log_and_print(
                20,
                f"After conversion check, file to upload is: {upload}",
            )
        else:
            upload = file[0]
            log_and_print(
                20,
                f"Publishing file from Media Browser: {upload}",
            )

        try:
            log_and_print(20, "Retrieving Slack access token")
            access_token = API(self.core).get_access_token()

        except Exception as e:
            log_and_print(
                40,
                f"Failed to retrieve Slack access token. Please check your configuration.\n\n{e}",
            )
            raise

        try:
            upload = upload.replace("\\", "/")

        except AttributeError:
            log_and_print(
                30,
                f"Upload path is not a string, cannot replace backslashes: {upload}. Passing... ",
            )
            pass

        if state_data["ui"] != "DL":
            log_and_print(
                10,
                "Publishing from non-Deadline UI, using QTimer to delay upload.",
            )
            QTimer.singleShot(
                0,
                lambda: self.upload_to_slack(
                    access_token=access_token,
                    file=upload,
                    state_data=state_data,
                    prism_user=prism_user,
                ),
            )
        else:
            log_and_print(10, "Publishing from a Deadline job.")
            self.upload_to_slack(
                access_token=access_token,
                file=upload,
                state_data=state_data,
                prism_user=prism_user,
            )

    # Upload file to Slack
    def upload_to_slack(
        self, access_token: str, file: str, state_data: dict, prism_user: str
    ):
        if state_data["ui"] == "Media":
            upload_dialog = UploadDialog()
            upload_dialog.show()

        current_project = f"{state_data['project']}"
        channel_id = get_channel_id(access_token, current_project)
        channel_users = get_channel_users(access_token, channel_id)
        slack_user = API(self.core).get_slack_user_id(prism_user, channel_users)

        comment = state_data["comments"]

        log_and_print(
            20,
            f"File: {file}\n\tState Data: {state_data}\n\tChannel ID: {channel_id}\n\tSlack User ID: {slack_user}",
        )

        upload_result = None
        try:
            # Upload the file to Slack
            upload_result = upload_content(
                access_token, channel_id, file, slack_user, comment
            )

            # Post the successful upload message
            uploaded = True
            if state_data["ui"] == "Media":
                upload_dialog.close()
                SuccessfulPOST(uploaded, state_data["ui"])
                log_and_print(20, "File uploaded to Slack successfully.")

        except Exception as e:
            uploaded = False
            log_and_print(40, f"Failed to upload file to Slack: {e}")
            if state_data["ui"] == "Media":
                SuccessfulPOST(uploaded, state_data["ui"])
                log_and_print(20, "File uploaded to Slack successfully.")

        versioninfo = state_data.get("versioninfo")
        try:
            versioninfo = versioninfo.as_posix()
        except AttributeError:
            pass

        files = (upload_result or {}).get("files") or []
        if not files:
            log_and_print(40, "Slack upload response did not include file metadata.")
            return

        file_id = files[0].get("id")

        timeout = 20
        timestamp = None

        while True:
            msg_history = get_channel_history(
                access_token=access_token, channel_id=channel_id, message_limit=30
            )
            timestamp = self._get_timestamp(file_id, msg_history)

            if timestamp is not None:
                log_and_print(
                    20,
                    f"Found message containing uploaded file with timestamp: {timestamp}",
                )
                break

            timeout -= 1
            log_and_print(
                20,
                f"Message containing uploaded file not found yet, retrying... Timeout in {timeout} seconds.",
            )
            time.sleep(2)

        if timeout <= 0:
            log_and_print(40, "Timed out waiting for message timestamp.")
            return

        self._apply_info_to_versioninfo(state_data=state_data, ts=timestamp)

    def _get_timestamp(self, file_id: str, messages: List[Dict[str, Any]]):
        """
        Retrieve the timestamp of the message containing the uploaded file.

        Args:
            file_id (str): The ID of the uploaded file.
            messages (List[Dict[str, Any]]): The list of messages from the channel history.

        Returns:
            str: The timestamp of the message containing the file, or None if not found.
        """

        for msg in messages or []:
            for m in msg.get("files") or []:
                if m.get("id") == file_id:
                    timestamp = msg.get("ts")
                    return timestamp

        return None

    def _apply_info_to_versioninfo(self, state_data: Dict, ts: str):
        """
        Apply Slack post information to the versioninfo file for the published version

        Args:
            state_data (dict): The state data containing the necessary information to publish the content to Slack, including the versioninfo file, status, ui, project name, etc.
            channel_id (str): The Slack Channel ID
            ts (str): The timestamp for the selected message on Slack
        """
        with open(state_data["versioninfo"], "r", encoding="utf-8") as f:
            versioninfo = json.load(f)

        try:
            # Add slack timestamp to versioninfo file
            if "slack" not in versioninfo:
                versioninfo["slack"] = {}
                versioninfo["slack"]["ts"] = ts

            with open(state_data["versioninfo"], "w") as f:
                json.dump(versioninfo, f, indent=4)
                log_and_print(
                    10,
                    f"Successfully applied Slack information to versioninfo file with state data: {state_data} and timestamp: {ts}",
                )

            return
        except Exception as e:
            log_and_print(
                40,
                f"Failed to apply Slack information to versioninfo file with state data: {state_data} and timestamp: {ts}\n\nError: {e}",
            )
            return
