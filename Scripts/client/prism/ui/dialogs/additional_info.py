import os
from pathlib import Path

from prism_slack.client.slack.slack_config import SlackConfig

from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
)


class AdditionalInfoDialog(QDialog):
    """
    Dialog to collect additional information from the user for Slack publishing.
    """

    def __init__(self, core: object):
        """
        Initialize the AdditionalInfoDialog.
        Args:
            core (object): The core application object.
        """

        super(AdditionalInfoDialog, self).__init__()

        plugin_directory = Path(__file__).resolve().parents[5]

        self.setWindowTitle("Slack Publish Information")
        self.setWindowIcon(QIcon(os.path.join(plugin_directory, "Resources", "slack-icon.png")))
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setModal(True)
        self.setLayout(QVBoxLayout())
        self.buttonLayout = QHBoxLayout()

        self.label = QLabel("Please leave your additional comments below (optional)")
        self.layout().addWidget(self.label)

        self.text_edit = QTextEdit()
        self.layout().addWidget(self.text_edit)

        self.button_ok = QPushButton("OK")
        self.button_cancel = QPushButton("Cancel")

        self.div = QFrame()
        self.div.setFrameShape(QFrame.HLine)
        self.div.setFrameShadow(QFrame.Sunken)
        self.layout().addWidget(self.div)

        if SlackConfig(core).load_config("studio")["slack"]["approvals"]["enabled"]:
            self.gb_status = QGroupBox("Status")
            self.bg_status = QButtonGroup()
            self.lo_review = QHBoxLayout()
            self.gb_status.setLayout(self.lo_review)

            self.rb_status_wip = QRadioButton("Work In Progress")
            self.rb_status_wip.setStyleSheet(
                """QRadioButton::indicator { width: 15px; height: 15px; }"""
            )
            self.rb_status_wip.setChecked(True)
            self.lo_review.addWidget(self.rb_status_wip)

            self.rb_status_reivew = QRadioButton("Request Review")
            self.rb_status_reivew.setStyleSheet(
                """QRadioButton::indicator { width: 15px; height: 15px; }"""
            )
            self.lo_review.addWidget(self.rb_status_reivew)

            self.bg_status.addButton(self.rb_status_wip)
            self.bg_status.addButton(self.rb_status_reivew)
            self.layout().addWidget(self.gb_status)

        self.buttonLayout.addWidget(self.button_ok)
        self.buttonLayout.addWidget(self.button_cancel)
        self.layout().addLayout(self.buttonLayout)

        self.button_ok.clicked.connect(self.accept)
        self.button_cancel.clicked.connect(self.reject)

    def get_comments(self):
        """
        Retrieve the comments entered by the user.

        Returns:
            str: The comments entered by the user.
        """

        return self.text_edit.toPlainText()

    def get_status(self):
        """
        Retrieve the selected status from the dialog.

        Returns:
            str: The selected status ("Work in Progress" or "Request Review").
        """

        if hasattr(self, "bg_status"):
            if self.rb_status_wip.isChecked():
                return "Work in Progress"
            elif self.rb_status_reivew.isChecked():
                return "Request Review"
        else:
            return "Work in Progress"
