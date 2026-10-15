from prism_slack.client.prism.api import API
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QWidget,
)

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


class StateManagerUI:
    def __init__(self, core):
        self.core = core

    # Create the Slack section of the State Manager UI
    @err_catcher(__name__)
    def createStateManagerSlackUI(self, state: object):
        state.cb_slackUserPool = QComboBox()
        state.cb_slackUserPool.setPlaceholderText("Select Artist")

        lo_slack_publish = QHBoxLayout()
        lo_slack_publish.setContentsMargins(10, 5, 0, 0)

        state.l_slackPublish = QLabel("Publish to Slack:")
        state.chb_slackPublish = QCheckBox()
        state.chb_slackPublish.setLayoutDirection(Qt.RightToLeft)

        lo_slack_notify = QHBoxLayout()
        lo_slack_notify.setContentsMargins(10, 5, 0, 0)

        state.l_slackNotify = QLabel("Notify Artist:")
        state.chb_slackNotify = QCheckBox()
        state.chb_slackNotify.setLayoutDirection(Qt.RightToLeft)

        if state.className != "Export" and state.className != "USD Export":
            lo_slack_publish.addWidget(state.l_slackPublish)
            lo_slack_publish.addWidget(state.chb_slackPublish)

        lo_slack_notify.addWidget(state.l_slackNotify)
        lo_slack_notify.addWidget(state.chb_slackNotify)
        lo_slack_notify.addWidget(state.cb_slackUserPool)

        lo_slack_approvals = QHBoxLayout()
        lo_slack_approvals.setContentsMargins(10, 5, 0, 0)
        state.l_approvals = QLabel("Status:")
        state.cb_approvals = QComboBox()
        state.cb_approvals.addItems(["Work in Progress", "Request Review"])

        if state.className != "Export" and state.className != "USD Export":
            lo_slack_approvals.addWidget(state.l_approvals)
            lo_slack_approvals.addWidget(state.cb_approvals)

        state.lo_slack_publish = lo_slack_publish
        state.lo_slack_notify = lo_slack_notify
        state.lo_slack_approvals = lo_slack_approvals

        if state.className != "Export" and state.className != "USD Export":
            state.gb_slack.layout().addLayout(lo_slack_publish)
        state.gb_slack.layout().addLayout(lo_slack_notify)

        if API(self.core).get_server_approvals() is True:
            state.gb_slack.layout().addLayout(lo_slack_approvals)

        lo_comments = QHBoxLayout()
        lo_comments.setContentsMargins(10, 5, 0, 0)

        if state.className != "Export" and state.className != "USD Export":
            state.te_slackComments = QTextEdit()
            state.te_slackComments.setPlaceholderText("(Optional) Leave your Slack comments here")
            lo_comments.addWidget(state.te_slackComments)

        state.gb_slack.layout().addLayout(lo_comments)

    # Remove the Slack section of the State Manager UI
    @err_catcher(__name__)
    def removeCleanupLayout(self, layout, attribute_name, state):
        if hasattr(state, attribute_name):
            sub_layout = getattr(state, attribute_name)
            if sub_layout:
                for i in reversed(range(sub_layout.count())):
                    item = sub_layout.itemAt(i)
                    if item.widget():
                        widget = item.widget()
                        sub_layout.removeWidget(widget)
                        widget.deleteLater()
                    elif item.layout():
                        sub_layout.removeItem(item)
                        item.deleteLater()

                layout.removeItem(sub_layout)
                sub_layout.deleteLater()

                delattr(state, attribute_name)

            for attr in [
                "chb_slackPublish",
                "l_slackPublish",
                "cb_slackUserPool",
                "l_slackNotify",
                "chb_slackNotify",
                "l_approvals",
                "cb_approvals",
                "te_slackComments",
            ]:
                if hasattr(state, attr):
                    widget = getattr(state, attr)
                    if isinstance(widget, QWidget):
                        widget.deleteLater()
                    delattr(state, attr)
