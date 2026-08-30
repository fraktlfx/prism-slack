from typing import Any

from prism_slack.client.prism.api import API
from prism_slack.client.slack.api import get_channel_id, get_channel_users, get_studio_users

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QGroupBox,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QWidget,
    QLayout,
)


def onAfterEffectsRenderDlgCreated(core: Any, dlg: QWidget):
    """Handle the creation of the AE Render Dialog and add Slack integration UI."""

    # Only build once
    if hasattr(dlg, "gb_slack"):
        return

    # ---- Groupbox shell ----
    dlg.gb_slack = QGroupBox("Slack")
    dlg.gb_slack.setCheckable(True)
    dlg.gb_slack.setChecked(False)
    dlg.gb_slack.setObjectName("gb_slack")
    dlg.gb_slack.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    dlg.lo_slack_group = QVBoxLayout(dlg.gb_slack)
    dlg.lo_slack_group.setContentsMargins(-1, 15, -1, -1)
    dlg.gb_slack.toggled.connect(lambda checked: _slack_toggle(core, dlg, checked))

    if not hasattr(dlg, "lo_main"):
        return

    bb_main = getattr(dlg, "bb_main")

    if bb_main is not None:
        idx = dlg.lo_main.indexOf(bb_main)

        if idx != -1:
            dlg.lo_main.insertWidget(idx, dlg.gb_slack)
            return

    dlg.lo_main.addWidget(dlg.gb_slack)


def _slack_toggle(core: Any, dlg: QWidget, checked: bool):
    """Toggle the Slack UI contents in the AE Render Dialog based on the group box state."""

    if checked:
        if getattr(dlg, "_slack_built", False):
            return
        _build_slack_contents(core, dlg)
        dlg._slack_built = True
    else:
        _clear_layout(dlg.lo_slack_group)
        dlg._slack_built = False


def _build_slack_contents(core: Any, dlg: QWidget):
    """
    Build the Slack UI contents in the AE Render Dialog.
    Args:
        core (Any): The core application object.
        dlg (QWidget): The AE Render Dialog object.
    """
    # Widgets
    dlg.cb_slackUserPool = QComboBox()
    dlg.cb_slackUserPool.setPlaceholderText("Select Artist")

    # Publish row
    row_pub = QHBoxLayout()
    row_pub.setContentsMargins(10, 5, 0, 0)
    dlg.l_slackPublish = QLabel("Publish to Slack:")
    dlg.chb_slackPublish = QCheckBox()
    dlg.chb_slackPublish.setLayoutDirection(Qt.RightToLeft)
    row_pub.addWidget(dlg.l_slackPublish)
    row_pub.addStretch()
    row_pub.addWidget(dlg.chb_slackPublish)

    # Notify row
    row_notify = QHBoxLayout()
    row_notify.setContentsMargins(10, 5, 0, 0)
    dlg.l_slackNotify = QLabel("Notify Artist:")
    dlg.chb_slackNotify = QCheckBox()
    dlg.chb_slackNotify.setLayoutDirection(Qt.RightToLeft)
    row_notify.addWidget(dlg.l_slackNotify)
    row_notify.addStretch()
    row_notify.addWidget(dlg.chb_slackNotify)
    row_notify.addWidget(dlg.cb_slackUserPool)

    _populate_user_pool(core, dlg)

    dlg.lo_slack_group.addLayout(row_pub)
    dlg.lo_slack_group.addLayout(row_notify)

    # Comments
    dlg.te_slackComments = QTextEdit()
    dlg.te_slackComments.setPlaceholderText("(Optional) Leave your Slack comments here")
    dlg.lo_slack_group.addWidget(dlg.te_slackComments)


def _clear_layout(layout: QLayout):
    """Safely deletes all items in a layout (widgets + nested layouts)."""

    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        lo = item.layout()
        if w is not None:
            w.setParent(None)
            w.deleteLater()
        elif lo is not None:
            _clear_layout(lo)
            lo.deleteLater()


def _populate_user_pool(core: Any, dlg: QWidget):
    """
    Populate the Slack user pool dropdown in the AE Render Dialog.

    Args:
        core (Any): The core application object.
        dlg (QWidget): The AE Render Dialog object.
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

        dlg.cb_slackUserPool.addItems(users)

    except Exception as e:
        print(f"Failed to populate user pool: {e}")
