import os
from pathlib import Path

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QVBoxLayout, QDialog, QLabel

# Create an "Uploading" dialog for the user to see while the file is being uploaded
class UploadDialog(QDialog):
    def __init__(self):
        super(UploadDialog, self).__init__()
        
        plugin_directory = Path(__file__).resolve().parents[5]
        
        self.setWindowTitle("Slack Upload")
        self.setWindowIcon(
            QIcon(os.path.join(plugin_directory, "Resources", "slack-icon.png"))
        )
        self.setModal(True)
        self.setLayout(QVBoxLayout())

        self.label = QLabel("Uploading to Slack...")
        self.layout().addWidget(self.label)
