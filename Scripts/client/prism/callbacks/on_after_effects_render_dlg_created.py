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

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


@err_catcher(__name__)
def onAfterEffectsRenderDlgCreated(core: object, dlg: QWidget):
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

    # ---- Insert into dialog (IMPORTANT) ----
    # Put it right above the button box if present, otherwise append
    if hasattr(dlg, "lo_main"):
        if hasattr(dlg, "bb_main"):
            idx = dlg.lo_main.indexOf(dlg.bb_main)
            if idx != -1:
                dlg.lo_main.insertWidget(idx, dlg.gb_slack)
            else:
                dlg.lo_main.addWidget(dlg.gb_slack)
        else:
            dlg.lo_main.addWidget(dlg.gb_slack)
    else:
        # last resort: do nothing / or raise
        return

    # Build contents lazily on toggle (optional)
    dlg.gb_slack.toggled.connect(lambda checked: _slack_toggle(core, dlg, checked))


@err_catcher(__name__)
def _slack_toggle(core: object, dlg: QWidget, checked: bool):
    if checked:
        if getattr(dlg, "_slack_built", False):
            return
        _build_slack_contents(core, dlg)
        dlg._slack_built = True
    else:
        # If you want to *remove* widgets when unchecked:
        _clear_layout(dlg.lo_slack_group)
        dlg._slack_built = False


@err_catcher(__name__)
def _build_slack_contents(core: object, dlg: QWidget):
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

    # Approvals row (conditional)
    if API(core).get_server_approvals() is True:
        row_appr = QHBoxLayout()
        row_appr.setContentsMargins(10, 5, 0, 0)
        dlg.l_approvals = QLabel("Status:")
        dlg.cb_approvals = QComboBox()
        dlg.cb_approvals.addItems(["Work in Progress", "Request Review"])
        row_appr.addWidget(dlg.l_approvals)
        row_appr.addWidget(dlg.cb_approvals)
        dlg.lo_slack_group.addLayout(row_appr)

    # Comments
    dlg.te_slackComments = QTextEdit()
    dlg.te_slackComments.setPlaceholderText("(Optional) Leave your Slack comments here")
    dlg.lo_slack_group.addWidget(dlg.te_slackComments)


def _clear_layout(layout: QLayout):
    """Safely deletes all items in a layout (widgets + nested layouts)."""
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        l = item.layout()
        if w is not None:
            w.setParent(None)
            w.deleteLater()
        elif l is not None:
            _clear_layout(l)
            l.deleteLater()


def _populate_user_pool(core: object, dlg: object):
    """
    Populate the Slack user pool dropdown in the AE Render Dialog.

    Args:
        core (object): The core application object.
        dlg (object): The AE Render Dialog object.
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
