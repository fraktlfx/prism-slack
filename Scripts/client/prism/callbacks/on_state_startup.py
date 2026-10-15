from prism_slack.client.prism.api import API
from prism_slack.client.prism.ui.state_manager_ui import StateManagerUI
from Scripts.client.prism.utils import log_and_print
from prism_slack.client.slack.api.get import get_channel_id, get_channel_users, get_studio_users

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QGroupBox, QVBoxLayout


def onStateStartup(core: object, state: object):
    """
    Add Slack publishing options to the State Manager on startup.

    Args:
        core (object): The core application object.

        state (object): The state object in the State Manager.
    """
    if state.className == "Playblast" or state.className == "Standalone USD Playblast":
        lo = state.gb_playblast.layout()
    elif state.className == "ImageRender":
        lo = state.gb_imageRender.layout()
    elif state.className == "LOP Render":
        lo = state.gb_general.layout()
    elif state.className == "Export" or state.className == "USD Export":
        if core.appPlugin.pluginName == "Houdini":
            lo = state.gb_general.layout()
        else:
            lo = state.gb_export.layout()
    else:
        return

    if core.appPlugin.pluginName == "Nuke":
        return

    if not hasattr(state, "gb_slack"):
        state.gb_slack = QGroupBox()
        state.gb_slack.setTitle("Slack")
        state.gb_slack.setCheckable(True)
        state.gb_slack.setChecked(False)
        state.gb_slack.setObjectName("gb_slack")
        state.gb_slack.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        lo_slack_group = QVBoxLayout()
        lo_slack_group.setContentsMargins(-1, 15, -1, -1)
        state.gb_slack.setLayout(lo_slack_group)

        state.gb_slack.toggled.connect(lambda toggled: _create_slack_submenu(core, toggled, state))
        state.gb_slack.toggled.connect(lambda toggled: state.stateManager.saveStatesToScene())

        lo.addWidget(state.gb_slack)


def _create_slack_submenu(core: object, toggled: bool, state: object):
    """
    Create the Slack submenu in the State Manager when toggled.

    Args:
        core (object): The core application object.
        toggled (bool): The toggled state of the Slack group box.
        state (object): The state object in the State Manager.
    """

    try:
        if toggled:
            if not hasattr(state, "cb_slackUserPool"):
                StateManagerUI(core).createStateManagerSlackUI(state)
                _populate_user_pool(core, state)
        else:
            layout = state.gb_slack.layout()
            StateManagerUI(core).removeCleanupLayout(layout, "lo_slack_publish", state)
            StateManagerUI(core).removeCleanupLayout(layout, "lo_slack_notify", state)
            if API(core).get_server_approvals() == "True":
                StateManagerUI(core).removeCleanupLayout(layout, "lo_slack_approvals", state)

    except Exception as e:
        log_and_print(40, f"Error creating Slack submenu: {e}")


def _populate_user_pool(core: object, state: object):
    """
    Populate the Slack user pool dropdown in the State Manager.

    Args:
        core (object): The core application object.
        state (object): The state object in the State Manager.
    """

    try:
        access_token = API(core).get_access_token()
        proj = API(core).get_current_project()
        channel_id = get_channel_id(access_token, proj)

        notify_user_pool = API(core).get_notify_user_pool().lower()

        users = []
        if notify_user_pool == "studio":
            users = get_studio_users(core=core)

        elif notify_user_pool == "channel":
            members = get_channel_users(access_token, channel_id)
            users = [member["display_name"] for member in members]

        state.cb_slackUserPool.addItems(users)

    except Exception as e:
        log_and_print(40, f"Failed to populate user pool: {e}")
