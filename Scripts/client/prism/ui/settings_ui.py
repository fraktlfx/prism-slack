import os
import webbrowser
from pathlib import Path

from prism_slack.client.prism.api import API
from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QAction,
)


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
            self._create_approvals_settings_menu(lo_slack, origin)
            self._create_server_settings_menu(lo_slack, origin)

            lo_slack.addStretch()

            self._create_links_section(lo_slack, origin)

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
            self._create_approvals_settings_menu(lo_slack, origin)
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
        slack_settings_tabs.addTab(self.approvals_settings_tab, "Approvals")
        slack_settings_tabs.addTab(self.server_settings_tab, "Server")
        slack_settings_tabs.addTab(self.tokens_settings_tab, "Tokens")

        if API(self.core).is_studio_loaded() is None:
            self.custom_channel_settings_tab = QWidget()
            slack_settings_tabs.addTab(
                self.custom_channel_settings_tab, "Custom Channel"
            )

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

            plugin_directory = Path(__file__).resolve().parents[4]
            slack_icon = os.path.join(plugin_directory, "Resources", "slack-icon.png")

            b_slack_signin = QPushButton("Sign in with Slack")
            b_slack_signin.setIcon(QIcon(slack_icon))
            b_slack_signin.setIconSize(b_slack_signin.iconSize())

            # Slack Sign-in button ---------
            lo_signin = QHBoxLayout()
            b_slack_signin.setFixedHeight(44)
            b_slack_signin.setMinimumWidth(260)
            b_slack_signin.setCursor(Qt.PointingHandCursor)
            b_slack_signin.setStyleSheet(
                """
                QPushButton {
                    color: #ffffff;
                    background-color: #4A154B;
                    border: 0;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-family: "Lato", sans-serif;
                    font-size: 16px;
                    font-weight: 600;
                    text-align: center;
                }
                QPushButton:hover { background-color: #5e1b61; }
                QPushButton:pressed { background-color: #3b0f3d; }
                QPushButton:disabled {
                    background-color:  #4A154B;
                    color: #ffffff;
                    opacity: 0.6;
                }
            """
            )
            origin.b_slack_signin = b_slack_signin

            b_slack_signout = QPushButton()
            b_slack_signout.setStyleSheet(
                """
                QPushButton {
                    color: #DBB071;
                    background-color: #1A1818;
                    border: 0;
                    border-radius: 6px;
                    padding: 12px 8px;
                    font-family: "Lato", sans-serif;
                    font-size: 16px;
                    font-weight: 600;
                    text-align: center;
                }
                """
            )
            logout_icon = os.path.join(plugin_directory, "Resources", "log-out.svg")
            b_slack_signout.setIcon(QIcon(logout_icon))
            # b_slack_signout.setMinimumHeight(100)
            origin.b_slack_signout = b_slack_signout

            lo_signin.addStretch()
            lo_signin.addWidget(origin.b_slack_signin)
            lo_signin.addWidget(origin.b_slack_signout)
            lo_signin.addStretch()

            lo_sites = QHBoxLayout()
            l_prism_slack = self._grab_prism_slack_logo()
            l_fraktl = self._grab_fraktl_logo()
            lo_sites.addWidget(l_prism_slack)
            lo_sites.addStretch()
            lo_sites.addWidget(l_fraktl)

            spacer = QSpacerItem(10, 5, QSizePolicy.Expanding, QSizePolicy.Minimum)
            lo_slackUserTab.addStretch()
            # if API(self.core).get_client_id() != "" or API(self.core).get_client_secret() != "":
            #     slack_id = API(self.core).get_prism_slack_user_id()
            #     if slack_id is None:
            lo_slackUserTab.addLayout(lo_signin)
            lo_slackUserTab.addSpacerItem(spacer)

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

        # -------- CLIENT ID ---------- #
        lo_slack_client_id = QHBoxLayout()

        l_slack_client_id = QLabel("Client ID: ")
        origin.l_slack_client_id = l_slack_client_id

        le_slack_client_id = QLineEdit()
        le_slack_client_id.setPlaceholderText("Input Client ID --->")
        le_slack_client_id.setEchoMode(QLineEdit.Password)
        le_slack_client_id.setReadOnly(True)
        le_slack_client_id.setFocusPolicy(Qt.NoFocus)
        le_slack_client_id.setContextMenuPolicy(Qt.NoContextMenu)
        origin.le_slack_client_id = le_slack_client_id

        b_slack_client_id = QPushButton("Input Client ID")
        origin.b_slack_client_id = b_slack_client_id

        lo_slack_client_id.addWidget(origin.l_slack_client_id)
        lo_slack_client_id.addWidget(origin.le_slack_client_id, 1)
        lo_slack_client_id.addWidget(origin.b_slack_client_id, 0, Qt.AlignBottom)

        lo_slack_token.addLayout(lo_slack_client_id)

        # -------- CLIENT SECRET ---------- #
        lo_slack_client_secret = QHBoxLayout()

        l_slack_client_secret = QLabel("Client Secret: ")
        origin.l_slack_client_secret = l_slack_client_secret

        le_slack_client_secret = QLineEdit()
        le_slack_client_secret.setPlaceholderText("Input Client Secret --->")
        le_slack_client_secret.setEchoMode(QLineEdit.Password)
        le_slack_client_secret.setReadOnly(True)
        le_slack_client_secret.setFocusPolicy(Qt.NoFocus)
        le_slack_client_secret.setContextMenuPolicy(Qt.NoContextMenu)
        origin.le_slack_client_secret = le_slack_client_secret

        b_slack_client_secret = QPushButton("Input Client Secret")
        origin.b_slack_client_secret = b_slack_client_secret

        lo_slack_client_secret.addWidget(origin.l_slack_client_secret)
        lo_slack_client_secret.addWidget(origin.le_slack_client_secret, 1)
        lo_slack_client_secret.addWidget(
            origin.b_slack_client_secret, 0, Qt.AlignBottom
        )

        lo_slack_token.addLayout(lo_slack_client_secret)

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
        lo_slack_app_level_token.addWidget(
            origin.b_slack_app_level_token, 0, Qt.AlignBottom
        )

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

        # --- Tag Artist --- #
        lo_tag_artist = QHBoxLayout()
        l_tag_artist = QLabel("Tag Artist: ")
        origin.chb_tag_artist = QCheckBox()
        origin.chb_tag_artist.setChecked(False)

        lo_tag_artist.addWidget(l_tag_artist)
        lo_tag_artist.addWidget(origin.chb_tag_artist)
        lo_tag_artist.addStretch()

        lo_slack_notifications.addLayout(lo_tag_artist)

        # --- User Pool --- #
        lo_notify_user_pool = QHBoxLayout()
        l_notify_method = QLabel("Notify Method:")
        l_notify_user_pool = QLabel("User Pool:")
        cb_notify_user_pool = QComboBox()
        cb_notify_user_pool.setPlaceholderText("Notify User Pool")
        origin.cb_notify_user_pool = cb_notify_user_pool

        l_notify_user_pool_help = self._grab_help_icon()
        l_notify_user_pool_help.setToolTip(
            """<p style='line-height:1;'>
                                        <span style='color:DodgerBlue;'><b>Studio</b></span>: Draw from the users in the Studio plugin pool<br>
                                        <br>
                                        <span style='color:Tomato;'><b>Channel</b></span>: Draw from the users in the Slack Project Channel<br>
                                        <br>
                                        <span style='color:MediumSeaGreen;'><b>Team</b></span>: Draw from the users in the Slack Team pool<br>
                                        <i>Note: If not kept up to date, your Team pool could be rather large</i>
                                        </p>"""
        )

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
        l_notify_method_help.setToolTip(
            """<p style='line-height:1;'>
                                        <span style='color:DodgerBlue;'><b>Direct</b></span>: Notify the selected user by Direct message<br>
                                        <br>
                                        <span style='color:Tomato;'><b>Channel</b></span>: Notify selected user in the Slack Channel<br>
                                        <br>
                                        <span style='color:MediumSeaGreen;'><b>Ephemeral Direct</b></span>: Notify the selected user in an ephemeral Direct message<br>
                                        <br>
                                        <span style='color:MediumSlateBlue;'><b>Ephemeral Channel</b></span>: Notify selected user in an ephemeral Channel message<br>
                                        </p>"""
        )

        lo_notify_method.addWidget(l_notify_method)
        lo_notify_method.addWidget(origin.cb_notify_method)
        lo_notify_method.addWidget(l_notify_method_help)
        lo_notify_method.addStretch()

        lo_slack_notifications.addLayout(lo_notify_method)

        lo_slack_notifications.addStretch()

    # Create Custom Channel Settings
    @err_catcher(__name__)
    def _create_custom_channel_settings(self, lo_slack, origin):
        plugin_directory = Path(__file__).resolve().parents[4]

        lo_custom_channel = QHBoxLayout()

        origin.l_custom_channel = QLabel("Channel Name: ")
        origin.le_custom_channel = QLineEdit()
        origin.le_custom_channel.setPlaceholderText("Enter the custom channel name")
        origin.le_custom_channel_action = QAction(
            origin.le_custom_channel,
            icon=QIcon(os.path.join(plugin_directory, "Resources", "not_verified.png")),
        )
        origin.le_custom_channel_action.setToolTip("Verification Status")
        origin.le_custom_channel.addAction(
            origin.le_custom_channel_action, QLineEdit.TrailingPosition
        )

        origin.b_custom_channel_verify = QPushButton("Verify")

        origin.l_custom_channel_help = self._grab_help_icon()
        origin.l_custom_channel_help.setToolTip(
            """
                                        <span>Enter the name of the custom channel you want to send notifications/publishes.</span>
            """
        )

        lo_custom_channel.addWidget(origin.l_custom_channel)
        lo_custom_channel.addWidget(origin.le_custom_channel)
        lo_custom_channel.addWidget(origin.b_custom_channel_verify)
        lo_custom_channel.addWidget(origin.l_custom_channel_help)
        lo_custom_channel.addStretch()

        if API(self.core).is_studio_loaded() is not None:
            gb_custom_channel = QGroupBox()
            gb_custom_channel.setTitle("Custom Channel")
            gb_custom_channel.setLayout(lo_custom_channel)
            lo_slack.addWidget(gb_custom_channel)
        else:
            # Add to custom channel settings tab (only exists when Studio plugin isn't loaded)
            if hasattr(self, "custom_channel_settings_tab"):
                self.custom_channel_settings_tab.setLayout(lo_custom_channel)

    # Create Approvals Settings Menu
    @err_catcher(name=__name__)
    def _create_approvals_settings_menu(self, lo_slack, origin):
        # --- Root Layout --- #
        lo_slack_approvals = QVBoxLayout()
        self.approvals_settings_tab.setLayout(lo_slack_approvals)
        lo_slack_approvals.setSpacing(10)
        lo_slack_approvals.setContentsMargins(12, 12, 12, 12)

        # --- Enable Approvals --- #
        lo_approvals_toggle = QHBoxLayout()
        l_approvals = QLabel("Enable: ")
        origin.chb_approvals = QCheckBox()
        origin.chb_approvals.setChecked(False)

        lo_approvals_toggle.addWidget(l_approvals)
        lo_approvals_toggle.addWidget(origin.chb_approvals)
        lo_approvals_toggle.addStretch()

        # --- Update Status Toggle --- #
        lo_update_status_toggle = QHBoxLayout()
        l_update_status = QLabel("Update Status: ")
        origin.chb_approvals_update_status = QCheckBox()
        origin.chb_approvals_update_status.setChecked(False)

        lo_update_status_toggle.addWidget(l_update_status)
        lo_update_status_toggle.addWidget(origin.chb_approvals_update_status)
        lo_update_status_toggle.addStretch()

        # --- Enable Usergroups --- #
        lo_usergroup_status = QHBoxLayout()
        l_usergroup_status = QLabel("Enable Usergroups: ")
        origin.chb_usergroup_status = QCheckBox()
        origin.chb_usergroup_status.setChecked(False)

        lo_usergroup_status.addWidget(l_usergroup_status)
        lo_usergroup_status.addWidget(origin.chb_usergroup_status)
        lo_usergroup_status.addStretch()

        # --- Usergroup Input --- #
        lo_approvals_usergroup = QHBoxLayout()
        l_approvals_usergroup = QLabel("Usergroup: ")
        origin.le_approvals_usergroup = QLineEdit()
        origin.le_approvals_usergroup.setPlaceholderText("Enter Approvals Usergroup")

        origin.b_approvals_usergroup = QPushButton("Verify")
        plugin_directory = Path(__file__).resolve().parents[4]
        i_verify = os.path.join(plugin_directory, "Resources", "not_verified.png")
        origin.b_approvals_usergroup.setIcon(QIcon(i_verify))

        lo_approvals_usergroup.addWidget(l_approvals_usergroup)
        lo_approvals_usergroup.addWidget(origin.le_approvals_usergroup)
        lo_approvals_usergroup.addWidget(origin.b_approvals_usergroup)
        lo_approvals_usergroup.addStretch()

        # --- Assemble --- #
        lo_slack_approvals.addLayout(lo_approvals_toggle)
        lo_slack_approvals.addLayout(lo_update_status_toggle)
        lo_slack_approvals.addLayout(lo_usergroup_status)
        lo_slack_approvals.addLayout(lo_approvals_usergroup)
        lo_slack_approvals.addStretch()

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

    # Grab the logout icon
    @err_catcher(__name__)
    def _grab_logout_icon(self):
        l_logout = QLabel()

        plugin_directory = Path(__file__).resolve().parents[4]
        i_logout = os.path.join(plugin_directory, "Resources", "log-out.svg")

        pixmap = QPixmap(i_logout)

        # Set pixmap to label and scale
        scale = 0.015
        l_logout.setPixmap(pixmap)
        l_logout.setScaledContents(True)
        l_logout.setFixedSize(pixmap.width() * scale, pixmap.height() * scale)
        l_logout.setContentsMargins(0, 0, 0, 0)

        return l_logout

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
        # plugin_directory = Path(__file__).resolve().parents[4]
        # i_verify = os.path.join(plugin_directory, "Resources", "not_verified.png")

        pixmap = QPixmap(l_verify)

        l_verify.setPixmap(pixmap)

        return l_verify

    @err_catcher(__name__)
    def _grab_prism_slack_logo(self):
        l_prism_slack = QLabel()

        plugin_directory = Path(__file__).resolve().parents[4]
        i_fraktl = os.path.join(
            plugin_directory, "Resources", "prism_slack_logo_studio_banner.png"
        )

        pixmap = QPixmap(i_fraktl)

        scale = 0.125
        l_prism_slack.setPixmap(pixmap)
        l_prism_slack.setScaledContents(True)
        l_prism_slack.setFixedSize(pixmap.width() * scale, pixmap.height() * scale)
        l_prism_slack.setCursor(Qt.CursorShape.PointingHandCursor)
        l_prism_slack.mousePressEvent = lambda e: webbrowser.open(
            "https://docs.fraktlfx.com/prism/slack/home"
        )

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
