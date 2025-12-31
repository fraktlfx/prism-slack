import os
import webbrowser
from pathlib import Path
from client.prism.api import API

from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTabWidget, QGroupBox

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


class SettingsUI:
    def __init__(self, core):
        super().__init__()
        self.core = core

    # Create the UI for the Slack plugin
    @err_catcher(__name__)
    def create_slack_studio_settings_ui(self, origin, settings):
        if not hasattr(origin, "w_slackStudioTab"):
            origin.w_slackStudioTab = QWidget()
            lo_slack = QVBoxLayout(origin.w_slackStudioTab)
            lo_slack.setSpacing(15)
            lo_slack.addStretch()

            self._create_settings_tabs(lo_slack, origin)

            self._create_slack_tokens_settings_menu(lo_slack, origin)
            self._create_notifications_publish_settings_menu(lo_slack, origin)
            self._create_server_settings_menu(lo_slack, origin)

            lo_slack.addStretch()

            lo_links = QHBoxLayout()
            l_prism_slack_logo = self._grab_prism_slack_logo()
            lo_links.addWidget(l_prism_slack_logo)
            lo_links.addStretch()
            lo_links.addWidget(self._grab_fraktl_logo())
            lo_slack.addLayout(lo_links)

            origin.addTab(origin.w_slackStudioTab, "Slack")

    # Create the Slack UI for the Project Settings
    @err_catcher(__name__)
    def create_slack_project_settings_ui(self, origin, settings):
        if not hasattr(origin, "w_slackProjectTab"):
            origin.w_slackProjectTab = QWidget()
            lo_slack = QVBoxLayout(origin.w_slackProjectTab)
            lo_slack.setSpacing(15)
            lo_slack.addStretch()

            self._create_settings_tabs(lo_slack, origin)

            self._create_slack_tokens_settings_menu(lo_slack, origin)
            self._create_notifications_publish_settings_menu(lo_slack, origin)
            self._create_custom_channel_settings(lo_slack, origin)
            self._create_server_settings_menu(lo_slack, origin)

            lo_slack.addStretch()

            self._create_links_section(lo_slack, origin)

            origin.addTab(origin.w_slackProjectTab, "Slack")


    def _create_settings_tabs(self, lo_slack, origin):
        slack_settings_tabs = QTabWidget()

        self.notification_settings_tab = QWidget()
        self.approvals_settings_tab = QWidget()
        self.server_settings_tab = QWidget()
        self.tokens_settings_tab = QWidget()

        lo_slack.addWidget(slack_settings_tabs)
        slack_settings_tabs.addTab(self.notification_settings_tab, "Notifications")
        slack_settings_tabs.addTab(self.server_settings_tab, "Server")
        slack_settings_tabs.addTab(self.tokens_settings_tab, "Tokens")
        if API(self.core).is_studio_loaded() is None:
            self.custom_channel_settings_tab = QWidget()
            slack_settings_tabs.addTab(self.custom_channel_settings_tab, "Custom Channel")

    # Create the Custom Channel UI for Project tab
    @err_catcher(__name__)
    def create_slack_custom_channel_ui(self, origin, settings):
        if not hasattr(origin, "w_slackCustomChannelTab"):
            origin.w_slackCustomChannelTab = QWidget()
            lo_slack = QVBoxLayout(origin.w_slackCustomChannelTab)

            self._create_custom_channel_settings(lo_slack, origin)

            origin.addTab(origin.w_slackCustomChannelTab, "Slack")

    # Create the User Settings UI
    @err_catcher(__name__)
    def create_user_settings_ui(self, origin):
        if not hasattr(origin, "w_slackUserTab"):
            origin.w_slackUserTab = QWidget()
            lo_slackUserTab = QVBoxLayout(origin.w_slackUserTab)

            lo_user = QHBoxLayout()
            l_user = QLabel("Display Name: ")
            le_user = QLineEdit()
            le_user.setPlaceholderText("Enter your Slack Display Name")
            origin.le_user = le_user

            i_userHelp = self._grab_help_icon()
            i_userHelp.setToolTip("""<p style='line-height:1;'>
                                    Input your Display Name, not your Full Name from your Slack Profile
                                    </p>""")

            lo_user.addWidget(l_user)
            lo_user.addWidget(origin.le_user)
            lo_user.addWidget(i_userHelp)

            lo_save = QHBoxLayout()

            lo_save.addStretch()
            b_userSave = QPushButton("Save")
            origin.b_userSave = b_userSave

            lo_save.addWidget(origin.b_userSave)
            lo_save.addStretch()

            lo_sites = QHBoxLayout()
            l_prism_slack = self._grab_prism_slack_logo()
            l_fraktl = self._grab_fraktl_logo()
            lo_sites.addWidget(l_prism_slack)
            lo_sites.addStretch()
            lo_sites.addWidget(l_fraktl)


            lo_slackUserTab.addStretch()
            lo_slackUserTab.addLayout(lo_user)
            lo_slackUserTab.addLayout(lo_save)
            lo_slackUserTab.addStretch()
            lo_slackUserTab.addLayout(lo_sites)

            origin.addTab(origin.w_slackUserTab, "Slack")

    # Create the Slack OAuth Token Settings Menu
    @err_catcher(__name__)
    def _create_slack_tokens_settings_menu(self, lo_slack, origin):
        lo_slack_token = QVBoxLayout()
        self.tokens_settings_tab.setLayout(lo_slack_token)

        # -------- BOT TOKEN ---------- #
        lo_slack_bot_token = QHBoxLayout()

        l_slack_bot_token = QLabel("Bot Token: ")
        origin.l_slack_bot_token = l_slack_bot_token

        le_slack_bot_token = QLineEdit()
        le_slack_bot_token.setPlaceholderText("Input Bot Token --->")
        le_slack_bot_token.setEchoMode(QLineEdit.Password)
        le_slack_bot_token.setReadOnly(True)
        le_slack_bot_token.setFocusPolicy(Qt.NoFocus)
        le_slack_bot_token.setContextMenuPolicy(Qt.NoContextMenu)
        origin.le_slack_bot_token = le_slack_bot_token

        b_slack_bot_token = QPushButton("Input Bot Token")
        origin.b_slack_bot_token = b_slack_bot_token

        lo_slack_bot_token.addWidget(origin.l_slack_bot_token)
        lo_slack_bot_token.addWidget(origin.le_slack_bot_token, 1)
        lo_slack_bot_token.addWidget(origin.b_slack_bot_token, 0, Qt.AlignBottom)

        lo_slack_token.addLayout(lo_slack_bot_token)

        # -------- APP-LEVEL TOKEN ---------- #
        lo_slack_app_level_token = QHBoxLayout()

        l_slack_app_level_token = QLabel("App-Level Token: ")
        origin.l_slack_app_level_token = l_slack_app_level_token

        le_slack_app_level_token = QLineEdit()
        le_slack_app_level_token.setPlaceholderText("Input App-Level Token --->")
        le_slack_app_level_token.setEchoMode(QLineEdit.Password)
        le_slack_app_level_token.setReadOnly(True)
        le_slack_app_level_token.setFocusPolicy(Qt.NoFocus)
        le_slack_app_level_token.setContextMenuPolicy(Qt.NoContextMenu)
        origin.le_slack_app_level_token = le_slack_app_level_token

        b_slack_app_level_token = QPushButton("Input App-Level Token")
        origin.b_slack_app_level_token = b_slack_app_level_token

        lo_slack_app_level_token.addWidget(origin.l_slack_app_level_token)
        lo_slack_app_level_token.addWidget(origin.le_slack_app_level_token, 1)
        lo_slack_app_level_token.addWidget(origin.b_slack_app_level_token, 0, Qt.AlignBottom)

        lo_slack_token.addLayout(lo_slack_app_level_token)

        lo_slack_token.addStretch()


    # Create the Notifications Settings Menu
    @err_catcher(name=__name__)
    def _create_notifications_publish_settings_menu(self, lo_slack, origin):
        # --- Root Layout --- #
        lo_slack_notifications = QVBoxLayout()
        self.notification_settings_tab.setLayout(lo_slack_notifications)
        lo_slack_notifications.setSpacing(10)
        lo_slack_notifications.setContentsMargins(12, 12, 12, 12)

        # --- User Pool --- #
        lo_notify_user_pool = QHBoxLayout()
        l_notify_method = QLabel("Notify Method:")
        l_notify_user_pool = QLabel("User Pool:")
        cb_notify_user_pool = QComboBox()
        cb_notify_user_pool.setPlaceholderText("Notify User Pool")
        origin.cb_notify_user_pool = cb_notify_user_pool

        l_notify_user_pool_help = self._grab_help_icon()
        l_notify_user_pool_help.setToolTip("""<p style='line-height:1;'>
                                        <span style='color:DodgerBlue;'><b>Studio</b></span>: Draw from the users in the Studio plugin pool<br>
                                        <br>
                                        <span style='color:Tomato;'><b>Channel</b></span>: Draw from the users in the Slack Project Channel<br>
                                        <br>
                                        <span style='color:MediumSeaGreen;'><b>Team</b></span>: Draw from the users in the Slack Team pool<br>
                                        <i>Note: If not kept up to date, your Team pool could be rather large</i>
                                        </p>""")

        lo_notify_user_pool.addWidget(l_notify_user_pool)
        lo_notify_user_pool.addWidget(origin.cb_notify_user_pool)
        lo_notify_user_pool.addWidget(l_notify_user_pool_help)
        lo_notify_user_pool.addStretch()

        lo_slack_notifications.addLayout(lo_notify_user_pool)

        # --- Notify Method --- #
        lo_notify_method = QHBoxLayout()
        l_notify_method = QLabel("Method: ")
        cb_notify_method = QComboBox()
        cb_notify_method.setPlaceholderText("Notify Method")
        origin.cb_notify_method = cb_notify_method

        l_notify_method_help = self._grab_help_icon()
        l_notify_method_help.setToolTip("""<p style='line-height:1;'>
                                        <span style='color:DodgerBlue;'><b>Direct</b></span>: Notify the selected user by Direct message<br>
                                        <br>
                                        <span style='color:Tomato;'><b>Channel</b></span>: Notify selected user in the Slack Channel<br>
                                        <br>
                                        <span style='color:MediumSeaGreen;'><b>Ephemeral Direct</b></span>: Notify the selected user in an ephemeral Direct message<br>
                                        <br>
                                        <span style='color:MediumSlateBlue;'><b>Ephemeral Channel</b></span>: Notify selected user in an ephemeral Channel message<br>
                                        </p>""")

        lo_notify_method.addWidget(l_notify_method)
        lo_notify_method.addWidget(origin.cb_notify_method)
        lo_notify_method.addWidget(l_notify_method_help)
        lo_notify_method.addStretch()

        lo_slack_notifications.addLayout(lo_notify_method)

        lo_slack_notifications.addStretch()


    # Create Custom Channel Settings
    @err_catcher(__name__)
    def _create_custom_channel_settings(self, lo_slack, origin):
        lo_custom_channel = QHBoxLayout()

        origin.l_custom_channel = QLabel("Channel Name: ")
        origin.le_custom_channel = QLineEdit()
        origin.le_custom_channel.setPlaceholderText("Enter the custom channel name")

        origin.b_custom_channel_verify = QPushButton("Verify")
        plugin_directory = Path(__file__).resolve().parents[4]
        i_verify = os.path.join(plugin_directory, "Resources", "not_verified.png")
        origin.b_custom_channel_verify.setIcon(QIcon(i_verify))

        origin.l_custom_channel_help = self._grab_help_icon()
        origin.l_custom_channel_help.setToolTip("""<p style='line-height:1;'>
                                        <span>Enter the name of the custom channel you want to send notifications/publishes. <br><br> </span>
                                        <span><i>NOTE: If you want to remove the custom channel, delete the text and press the verify button again</i></span>
                                        </p>""")

        lo_custom_channel.addWidget(origin.l_custom_channel)
        lo_custom_channel.addWidget(origin.le_custom_channel)
        lo_custom_channel.addWidget(origin.b_custom_channel_verify)
        lo_custom_channel.addWidget(origin.l_custom_channel_help)
        lo_custom_channel.addStretch()

        if API(self.core).is_studio_loaded() is not None:
            gb_custom_channel = QGroupBox()
            gb_custom_channel.setTitle("Custom Channel")
            gb_custom_channel.setContentsMargins(0, 30, 0, 0)
            gb_custom_channel.setLayout(lo_custom_channel)
            lo_slack.addWidget(gb_custom_channel)
        else:
            # Add to custom channel settings tab (only exists when Studio plugin isn't loaded)
            if hasattr(self, "custom_channel_settings_tab"):
                self.custom_channel_settings_tab.setLayout(lo_custom_channel)


    # Create the Server Settings Menu
    @err_catcher(name=__name__)
    def _create_server_settings_menu(self, lo_slack, origin):
        # --- Root Layout --- #
        lo_slack_server = QVBoxLayout()
        self.server_settings_tab.setLayout(lo_slack_server)

        # lo_server = QVBoxLayout()
        lo_slack_server.setSpacing(8)
        lo_slack_server.setContentsMargins(12, 8, 12, 12)

        # --- Status Row --- #
        lo_status = QHBoxLayout()
        lo_status.setSpacing(6)

        l_server_status = QLabel("Status:")
        l_server_status_value = QLabel("Offline")
        f_status = l_server_status_value.font()
        f_status.setItalic(True)
        l_server_status_value.setFont(f_status)
        origin.l_server_status_value = l_server_status_value

        lo_status.addWidget(l_server_status)
        lo_status.addWidget(origin.l_server_status_value)
        lo_status.addStretch()

        origin.b_server = QPushButton("Start Server")
        origin.b_reset_server = QPushButton("Reset Server")

        lo_status.addWidget(origin.b_server)
        lo_status.addWidget(origin.b_reset_server)

        # --- Machine Row --- #
        lo_machine = QHBoxLayout()
        lo_machine.setSpacing(6)

        l_machine = QLabel("Machine:")
        l_machine_value = QLabel("---------")
        f_machine = l_machine_value.font()
        f_machine.setItalic(True)
        l_machine_value.setFont(f_machine)
        origin.l_machine_value = l_machine_value

        lo_machine.addWidget(l_machine)
        lo_machine.addWidget(origin.l_machine_value)
        lo_machine.addStretch()

        # --- Assemble --- #
        lo_slack_server.addLayout(lo_status)
        lo_slack_server.addLayout(lo_machine)

        lo_slack_server.addStretch()

    def _create_links_section(self, lo_slack, origin):
        lo_links = QHBoxLayout()
        l_prism_slack_logo = self._grab_prism_slack_logo()
        l_fraktl_logo = self._grab_fraktl_logo()

        lo_links.addWidget(l_prism_slack_logo)
        lo_links.addStretch()
        lo_links.addWidget(l_fraktl_logo)

        lo_slack.addLayout(lo_links)

    # Grab the Slack logo
    @err_catcher(__name__)
    def _grab_slack_logo(self):
        l_slack = QLabel()

        plugin_directory = Path(__file__).resolve().parents[4]
        i_slack = os.path.join(plugin_directory, "Resources", "slack-icon.png")

        pixmap = QPixmap(i_slack)

        # Set pixmap to label and scale
        scale = 0.015
        l_slack.setPixmap(pixmap)
        l_slack.setScaledContents(True)
        l_slack.setFixedSize(pixmap.width() * scale, pixmap.height() * scale)
        l_slack.setContentsMargins(0, 0, 0, 0)

        return l_slack

    # Grab the Help Icon
    @err_catcher(__name__)
    def _grab_help_icon(self):
        l_help = QLabel()
        help_icon = os.path.join(
            self.core.prismLibs, "Scripts", "UserInterfacesPrism", "help.png"
        )

        pixmap = QPixmap(help_icon)

        l_help.setPixmap(pixmap)

        return l_help

    # Grab verify icon
    def _grab_verify_icon(self):
        l_verify = QLabel()
        plugin_directory = Path(__file__).resolve().parents[4]
        i_verify = os.path.join(plugin_directory, "Resources", "not_verified.png")

        pixmap = QPixmap(l_verify)

        l_verify.setPixmap(pixmap)

        return l_verify

    @err_catcher(__name__)
    def _grab_prism_slack_logo(self):
        l_prism_slack = QLabel()

        plugin_directory = Path(__file__).resolve().parents[4]
        i_fraktl = os.path.join(plugin_directory, "Resources", "prism_slack_logo_community_banner.png")

        pixmap = QPixmap(i_fraktl)

        scale = 0.125
        l_prism_slack.setPixmap(pixmap)
        l_prism_slack.setScaledContents(True)
        l_prism_slack.setFixedSize(pixmap.width() * scale, pixmap.height() * scale)
        l_prism_slack.setCursor(Qt.CursorShape.PointingHandCursor)
        l_prism_slack.mousePressEvent = lambda e: webbrowser.open("https://docs.fraktlfx.com/prism/slack/home")

        return l_prism_slack
    
    @err_catcher(__name__)
    def _grab_fraktl_logo(self):
        l_fraktl = QLabel()

        plugin_directory = Path(__file__).resolve().parents[4]
        i_fraktl = os.path.join(plugin_directory, "Resources", "fraktl-logo.svg")

        pixmap = QPixmap(i_fraktl)

        scale = 0.125
        l_fraktl.setPixmap(pixmap)
        l_fraktl.setScaledContents(True)
        l_fraktl.setFixedSize(pixmap.width() * scale, pixmap.height() * scale)
        l_fraktl.setCursor(Qt.CursorShape.PointingHandCursor)
        l_fraktl.mousePressEvent = lambda e: webbrowser.open("https://fraktlfx.com")

        return l_fraktl