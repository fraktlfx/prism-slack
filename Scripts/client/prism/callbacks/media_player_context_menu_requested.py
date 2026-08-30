import os
import json
import webbrowser
from pathlib import Path

from prism_slack.client.prism.api import API
from prism_slack.client.prism.utils import log_and_print
from prism_slack.client.prism.ui import AdditionalInfoDialog
from prism_slack.client.slack.publish import Publish
from prism_slack.client.slack.api import get_channel_id, get_permalink

from qtpy.QtWidgets import QDialog, QAction, QWidget


def mediaPlayerContextMenuRequested(core: object, origin: object, menu: QWidget):
    """
    Add "Publish to Slack" option to the media player's context menu.

    Args:
        core (Any): The core application object.
        origin (Any): The origin object requesting the context menu.
        menu (Any): The context menu object to which the option will be added.
    """
    if not type(origin.origin).__name__ == "MediaBrowser":
        return

    pluginDirectory = Path(__file__).resolve().parents[4]
    iconPath = os.path.join(pluginDirectory, "Resources", "slack-icon.png")
    icon = core.media.getColoredIcon(iconPath)

    file = origin.seq

    version_folder = API(core).get_version_folder(file)
    versioninfo = version_folder / "versioninfo.json"
    log_and_print(10, f"Version info path: {versioninfo}")

    if not versioninfo.exists():
        log_and_print(
            20,
            f"Versioninfo.json not found at {versioninfo}. Creating one with empty values.",
        )

        versioninfo_data = "{}"
        with open(versioninfo, "w", encoding="utf-8") as f:
            f.write(versioninfo_data)

    with open(versioninfo, "r", encoding="utf-8") as f:
        data = json.load(f)

    state_data = {
        "project": API(core).get_current_project(),
        "state_type": "Media",
        "ui": "Media",
        "app": "Standalone",
        "versioninfo": versioninfo,
    }

    if "slack" not in data:
        action = QAction("Publish to Slack", origin)
        action.triggered.connect(
            lambda: _get_comments(
                core=core,
                file=file,
                state_data=state_data,
                prism_user=API(core).get_prism_slack_username(),
            )
        )
    else:
        action = QAction("View in Slack", origin)
        action.triggered.connect(
            lambda: _view_in_slack(core=core, state_data=state_data, data=data)
        )

    menu.insertAction(menu.actions()[-1], action)
    action.setIcon(icon)


def _get_comments(core: object, file: str, state_data: dict, prism_user: str):
    """
    Open a dialog to get additional comments and status before publishing to Slack.

    Args:
        core (object): The core application object.
        file (str): The file path to be published.
        state_data (dict): The state data dictionary to be updated with comments and status.
    """
    info_dialog = AdditionalInfoDialog(core)

    if info_dialog.exec_() == QDialog.Accepted:
        comment = info_dialog.get_comments()
        state_data["comments"] = comment

        info_dialog.close()

    else:
        info_dialog.close()
        return

    log_and_print(
        10,
        f"""Collected information for Slack Publish through Project Browser context menu:
                File: {file}
                State Data: {state_data}
                Prism User: {prism_user}
                """,
    )
    Publish(core).publish_to_slack(file, state_data, prism_user)


def _view_in_slack(core: object, state_data: dict, data: dict):
    """
    Open the published file in Slack using the timestamp to generate a permalink and open a web browser/slack app to the location.
    Args:
        core (object): The core application object.
        state_data (dict): The state data dictionary containing project information.
        data (dict): The data loaded from versioninfo.json containing Slack information.
    """
    access_token = API(core).get_access_token()
    project = state_data["project"]
    channel_id = get_channel_id(access_token=access_token, project_name=project)
    timestamp = data["slack"]["ts"]

    permalink = get_permalink(
        access_token=access_token, channel_id=channel_id, ts=timestamp
    )

    webbrowser.open(permalink)
