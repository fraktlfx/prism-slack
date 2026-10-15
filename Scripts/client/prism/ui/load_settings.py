import os
from pathlib import Path

from prism_slack.client.prism.api import API
from prism_slack.client.prism.ui import InputDialog
from prism_slack.client.slack.api.get import get_usergroups
from prism_slack.client.slack.slack_config import SlackConfig
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QDialog
from prism_slack.server.controls import ServerControls

pcore = None


def load_settings(core, origin, settings):
    global pcore
    pcore = core

    _set_options(origin)
    _connect_events(origin)


# -----------
# Set the Slack options in the studio/project settings window
# -----------
def _set_options(origin):
    # Check for the slack bot and app-level tokens. Also check for the client id and client secret and assign them in the ui
    _check_token(origin)
    _check_client_id(origin)
    _check_client_secret(origin)
    _check_app_level_token(origin)

    # Check whether to tag the artist when publishing to Slack
    _check_tag_artist(origin)

    # Add current methods for notifications and set the current method in the ui
    _add_notify_methods(origin)
    _check_notify_method(origin)

    # Add the current user pools for notifications and set the current user pool in the ui
    _add_notify_user_pools(origin)
    _check_notify_user_pool(origin)

    # Check the approvals options and the usergroups
    _check_approvals(origin)
    _check_approvals_update_status(origin)
    _check_approvals_usergroup_status(origin)
    _check_approvals_usergroup(origin)

    ServerControls(pcore).check_server_status(origin)


# Connect the events in the studio/project settings window
def _connect_events(origin):
    origin.b_slack_bot_token.clicked.connect(
        lambda _checked=False: _input_token(origin)
    )
    origin.b_slack_client_id.clicked.connect(
        lambda _checked=False: _input_client_id(origin)
    )
    origin.b_slack_client_secret.clicked.connect(
        lambda _checked=False: _input_client_secret(origin)
    )
    origin.b_slack_app_level_token.clicked.connect(
        lambda _checked=False: _input_app_level_token(origin)
    )

    origin.chb_tag_artist.toggled.connect(lambda _checked: _toggle_tag_artist(origin))
    origin.cb_notify_user_pool.currentIndexChanged.connect(
        lambda index: _update_notify_user_pool(origin, index)
    )
    origin.cb_notify_method.currentIndexChanged.connect(
        lambda index: _update_notify_method(origin, index)
    )

    origin.b_server.clicked.connect(
        lambda _checked=False: ServerControls(pcore).toggle_server(origin)
    )
    origin.b_reset_server.clicked.connect(
        lambda: ServerControls(pcore).gui_reset_server_status(origin)
    )
    origin.chb_approvals.toggled.connect(lambda _checked: _approvals_toggle(origin))
    origin.chb_approvals_update_status.toggled.connect(
        lambda _checked: _approvals_update_status_toggle(origin)
    )
    origin.chb_usergroup_status.toggled.connect(
        lambda _checked: _usergroup_toggle(origin)
    )
    origin.b_approvals_usergroup.clicked.connect(
        lambda _checked=False: _verify_approvals_usergroup(origin)
    )


# -----------
# Pop up a dialog to input the Slack API token
# -----------
def _input_token(origin):
    input_dialog = InputDialog(title="Enter your Slack Bot API Token")
    if input_dialog.exec_() == QDialog.Accepted:
        slack_token = input_dialog.get_input()
        origin.le_slack_bot_token.setText(slack_token)

        # Save the token to the config file
        config = SlackConfig(pcore).load_config(mode="studio")
        config["slack"]["tokens"]["bot_token"] = slack_token
        SlackConfig(pcore).save_config_setting(config, mode="studio")


def _input_client_id(origin):
    input_dialog = InputDialog(title="Enter your Slack Client ID")
    if input_dialog.exec_() == QDialog.Accepted:
        client_id = input_dialog.get_input()
        origin.le_slack_client_id.setText(client_id)

        # Save the client id to the config file
        config = SlackConfig(pcore).load_config(mode="studio")
        config["slack"]["tokens"]["client_id"] = client_id
        SlackConfig(pcore).save_config_setting(config, mode="studio")


def _input_client_secret(origin):
    input_dialog = InputDialog(title="Enter your Slack Client Secret")
    if input_dialog.exec_() == QDialog.Accepted:
        client_secret = input_dialog.get_input()
        origin.le_slack_client_secret.setText(client_secret)

        # Save the client secret to the config file
        config = SlackConfig(pcore).load_config(mode="studio")
        config["slack"]["tokens"]["client_secret"] = client_secret
        SlackConfig(pcore).save_config_setting(config, mode="studio")


# Input the App-Level Token in the project/studio settings Window
def _input_app_level_token(origin):
    input_dialog = InputDialog(title="Enter your Slack App-Level Token")
    if input_dialog.exec_() == QDialog.Accepted:
        app_token = input_dialog.get_input()
        origin.le_slack_app_level_token.setText(app_token)

        config = SlackConfig(pcore).load_config(mode="studio")
        config["slack"]["tokens"]["app_token"] = app_token

        SlackConfig(pcore).save_config_setting(config, mode="studio")


# Check if the Slack Bot token is present in the pipeline configuration file
def _check_token(origin):
    token = API(pcore).get_access_token()

    if token == "":
        origin.le_slack_bot_token.setPlaceholderText("Enter your Slack API Token --->")
    else:
        origin.le_slack_bot_token.setText(token)


# Check if the Slack Client ID is present in the pipeline configuration file
def _check_client_id(origin):
    client_id = API(pcore).get_client_id()

    if client_id == "":
        origin.le_slack_client_id.setPlaceholderText("Enter your Slack Client ID --->")
    else:
        origin.le_slack_client_id.setText(client_id)


# Check if the Slack Client Secret is present in the pipeline configuration file
def _check_client_secret(origin):
    client_secret = API(pcore).get_client_secret()

    if client_secret == "":
        origin.le_slack_client_secret.setPlaceholderText(
            "Enter your Slack Client ID --->"
        )
    else:
        origin.le_slack_client_secret.setText(client_secret)


# Check the App-Level token in the project/studio config file
def _check_app_level_token(origin):
    app_token = API(pcore).get_app_level_token()

    if app_token != "":
        origin.le_slack_app_level_token.setText(app_token)

    else:
        origin.le_slack_app_level_token.setPlaceholderText(
            "Enter your Slack App-Level Token"
        )


# Check whether or not to tag the artist on publishes to Slack
def _check_tag_artist(origin):
    tag_artist = API(pcore).get_tag_artist()

    if tag_artist:
        origin.chb_tag_artist.setChecked(True)
    else:
        origin.chb_tag_artist.setChecked(False)


# Toggle the tag artist setting in the config file
def _toggle_tag_artist(origin):
    tag_artist = API(pcore).get_tag_artist()
    config = SlackConfig(pcore).load_config(mode="studio")

    if tag_artist is False:
        config["slack"]["notifications"]["tag_artist"] = True
    if tag_artist:
        config["slack"]["notifications"]["tag_artist"] = False

    SlackConfig(pcore).save_config_setting(config, mode="studio")


# Add notification methods to the dropdown in the studio/project settings Slack window
def _add_notify_methods(origin):
    methods = ["Direct", "Channel", "Ephemeral Direct", "Ephemeral Channel"]

    origin.cb_notify_method.addItems(methods)


# Change the notification method in the studio/project settings Slack window
def _update_notify_method(origin, index):
    config = SlackConfig(pcore).load_config("studio")

    config["slack"]["notifications"]["method"] = origin.cb_notify_method.currentText()

    SlackConfig(pcore).save_config_setting(config, "studio")


# Check the notification method in the studio/project settings Slack window
def _check_notify_method(origin):
    notify_method = API(pcore).get_notify_user_method()

    if notify_method != "":
        origin.cb_notify_method.setCurrentText(notify_method)

    else:
        return


# Add the user pools used for notifications to the dropdown in the studio/project settings Slack window
def _add_notify_user_pools(origin):
    user_pool = []
    # Disabling the Studio user pool for now until I set a better method for acquiring all studio Display Names
    # if pcore.getPlugin("Studio"):
    #     user_pool.append("Studio")
    user_pool.append("Channel")

    origin.cb_notify_user_pool.addItems(user_pool)


# Update the user pools used for notifications in the studio/project settings Slack window
def _update_notify_user_pool(origin, index):
    config = SlackConfig(pcore).load_config("studio")

    config["slack"]["notifications"]["user_pool"] = (
        origin.cb_notify_user_pool.currentText()
    )

    SlackConfig(pcore).save_config_setting(config, "studio")


# Check the method of notification to Slack users
def _check_notify_user_pool(origin):
    notify_user_pool = API(pcore).get_notify_user_pool()

    if notify_user_pool != "":
        origin.cb_notify_user_pool.setCurrentText(notify_user_pool)

    else:
        return


# Toggle the server approvals in the project/studio settings window
def _approvals_toggle(origin):
    server_approvals = API(pcore).get_server_approvals()
    config = SlackConfig(pcore).load_config(mode="studio")

    if server_approvals is False:
        config["slack"]["approvals"]["enabled"] = True

    if server_approvals is True:
        config["slack"]["approvals"]["enabled"] = False

    SlackConfig(pcore).save_config_setting(config, mode="studio")


# Check the server approvals in the project/studio settings window
def _check_approvals(origin):
    server_approvals = API(pcore).get_server_approvals()

    if server_approvals is True:
        origin.chb_approvals.setChecked(True)
    else:
        origin.chb_approvals.setChecked(False)


# Toggle enabling update status on publishes
def _approvals_update_status_toggle(origin):
    update_status = API(pcore).get_approvals_update_status()
    config = SlackConfig(pcore).load_config(mode="studio")

    if update_status is False:
        config["slack"]["approvals"]["update_status"] = True

    if update_status is True:
        config["slack"]["approvals"]["update_status"] = False

    SlackConfig(pcore).save_config_setting(config, mode="studio")


# Check enabling update status on publishes
def _check_approvals_update_status(origin):
    update_status = API(pcore).get_approvals_update_status()

    if update_status is True:
        origin.chb_approvals_update_status.setChecked(True)
    else:
        origin.chb_approvals_update_status.setChecked(False)


# Toggle enabling the usergroups for Slack
def _usergroup_toggle(origin):
    usergroup_status = API(pcore).get_approvals_usergroup_status()
    config = SlackConfig(pcore).load_config(mode="studio")

    if usergroup_status is False:
        config["slack"]["approvals"]["enable_usergroup"] = True
    if usergroup_status:
        config["slack"]["approvals"]["enable_usergroup"] = False

    SlackConfig(pcore).save_config_setting(config, mode="studio")


# Check whether the approvals usergroup status is enabled
def _check_approvals_usergroup_status(origin):
    usergroup_status = API(pcore).get_approvals_usergroup_status()

    if usergroup_status:
        origin.chb_usergroup_status.setChecked(True)
    else:
        origin.chb_usergroup_status.setChecked(False)


# Check the usergroup that will be used in approvals
def _check_approvals_usergroup(origin):
    usergroup = API(pcore).get_approvals_usergroup()

    if usergroup != "":
        origin.le_approvals_usergroup.setText(usergroup)

        plugin_directory = Path(__file__).resolve().parents[4]
        i_verified = os.path.join(plugin_directory, "Resources", "running.png")

        origin.b_approvals_usergroup.setIcon(QIcon(i_verified))
        origin.b_approvals_usergroup.setText("Verified")
    else:
        origin.le_approvals_usergroup.setPlaceholderText("Enter a usergroup")


# Verify the approvals usergroup exists on Slack
def _verify_approvals_usergroup(origin):
    input_usergroup = origin.le_approvals_usergroup.text()
    plugin_directory = Path(__file__).resolve().parents[4]

    if input_usergroup == "":
        i_not_verified = os.path.join(plugin_directory, "Resources", "not_verified.png")

        origin.le_approvals_usergroup.setPlaceholderText("Enter a usergroup")
        origin.b_approvals_usergroup.setIcon(QIcon(i_not_verified))

        config = SlackConfig(pcore).load_config(mode="studio")
        config["slack"]["approvals"]["usergroup"] = ""
        SlackConfig(pcore).save_config_setting(config, mode="studio")

    else:
        token = API(pcore).get_access_token()
        if token != "":
            usergroups = get_usergroups(token)

            if usergroups is not None:
                for u in usergroups:
                    if u["name"].lower() == input_usergroup.lower():
                        i_verified = os.path.join(
                            plugin_directory,
                            "Resources",
                            "running.png",
                        )

                        origin.b_approvals_usergroup.setIcon(QIcon(i_verified))
                        origin.b_approvals_usergroup.setText("Verified")
                        origin.le_approvals_usergroup.setText(input_usergroup)

                        # Save the usergroup to the config file
                        config = SlackConfig(pcore).load_config(mode="studio")
                        config["slack"]["approvals"]["usergroup"] = input_usergroup
                        SlackConfig(pcore).save_config_setting(config, mode="studio")

                    elif pcore is not None:
                        pcore.popup(f"{input_usergroup} usergroup is not valid")
