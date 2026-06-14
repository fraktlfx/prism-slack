from Scripts.client.slack.api import (
    get_channel_users,
    get_studio_users,
    get_channel_id,
)

from client.prism.utils import log_and_print
from Scripts.client.prism.ui.state_manager_ui import StateManagerUI
from Scripts.client.prism.api import API

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QGroupBox, QVBoxLayout


def onStateStartup(core: object, state: object):
    # Add Slack publishing options to the State Manager
    if state.className == "Playblast":
        lo = state.gb_playblast.layout()
    elif state.className == "ImageRender":
        lo = state.gb_imageRender.layout()
    elif state.className == "Export":
        if core.appPlugin.pluginName == "Houdini":
            lo = state.gb_general.layout()
        else:
            lo = state.gb_export.layout()
    else:
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

        state.gb_slack.toggled.connect(
            lambda toggled: _create_slack_submenu(core, toggled, state)
        )

        lo.addWidget(state.gb_slack)


def _create_slack_submenu(core: object, toggled: bool, state: object):
    try:
        state_manager_ui = StateManagerUI(core)
        # If the group box is toggled on
        if toggled:
            if not hasattr(state, "cb_slackUserPool"):
                state_manager_ui.createStateManagerSlackUI(state)
                _populate_user_pool(core, state)
        else:
            layout = state.gb_slack.layout()
            state_manager_ui.removeCleanupLayout(layout, "lo_slack_publish", state)
            state_manager_ui.removeCleanupLayout(layout, "lo_slack_notify", state)

    except Exception as e:
        log_and_print(40, f"Failed to create Slack submenu. Error: {e}")
        return


def _populate_user_pool(core: object, state: object):
    api = API(core)
    try:
        access_token = api.get_access_token()
        proj = api.get_current_project()
        channel_id = get_channel_id(access_token, proj)

        notify_user_pool = api.get_notify_user_pool().lower()

        users = []
        if notify_user_pool == "studio":
            users = get_studio_users()

        elif notify_user_pool == "channel":
            members = get_channel_users(access_token, channel_id)
            users = [member["display_name"] for member in members]

        state.cb_slackUserPool.addItems(users)

    except Exception as e:
        log_and_print(40, f"Failed to populate Slack user pool. Error: {e}")
        return
