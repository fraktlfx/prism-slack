from pathlib import Path

from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout


class SignInDialog(QDialog):
    """
    Dialog that lets the user 'Sign in with Slack'. On success, it writes
    user_id / username into the user config and closes with Accepted.
    """

    def __init__(self, login, parent=None):
        super().__init__(parent)
        self.login = login
        self.result_user = None

        plugin_directory = Path(__file__).resolve().parents[5]
        slack_icon = str(plugin_directory / "Resources" / "slack-icon.png")

        self.setWindowTitle("Slack")
        self.setWindowIcon(QIcon(slack_icon))
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Button
        self.b_slack_signin = QPushButton("Sign in with Slack", self)
        self.b_slack_signin.setIcon(QIcon(slack_icon))
        self.b_slack_signin.setFixedHeight(44)
        self.b_slack_signin.setMinimumWidth(260)
        self.b_slack_signin.setCursor(Qt.PointingHandCursor)
        self.b_slack_signin.setStyleSheet(
            """
            QPushButton {
                color: #ffffff;
                background-color: #4A154B;
                border: 0;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover   { background-color: #5e1b61; }
            QPushButton:pressed { background-color: #3b0f3d; }
            QPushButton:disabled { background-color: #4A154B; color: #ffffff; opacity: 0.6; }
        """
        )

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.b_slack_signin)
        row.addStretch()
        layout.addLayout(row)

        self.status = QLabel("", self)
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)
        layout.addStretch()

        self.b_slack_signin.clicked.connect(self._on_signin_clicked)

    def _on_signin_clicked(self):
        try:
            user = self.login()
            if not user:
                QMessageBox.warning(self, "Slack", "Sign-in was cancelled or failed.")
                return
            self.result_user = user
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Slack Sign-in Error", str(e))
