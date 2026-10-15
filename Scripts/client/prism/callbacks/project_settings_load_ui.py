from prism_slack.client.prism.api import API
from prism_slack.client.prism.ui.settings_ui import SettingsUI
from prism_slack.client.prism.ui.load_settings import load_settings
from prism_slack.client.prism.ui.load_custom_channel_settings import load_custom_channel_settings

from prism_slack.client.slack.slack_config import SlackConfig

from qtpy.QtWidgets import QWidget


def projectSettings_loadUI(core: object, origin: QWidget):
    """
    Load the Slack UI in the project settings window.

    Args:
        core (object): The core application object.
        origin (QWidget): The origin QWidget (project settings window).
    """

    settings = SettingsUI(core)

    config = SlackConfig(core).load_config(mode="studio")
    SlackConfig(core).check_slack_studio_options(config)

    if API(core).is_studio_loaded():
        if (
            core.getPlugin("Studio").getStudioConfigPath() is None
            or core.getPlugin("Studio").isStudioActive() is False
        ):
            settings.create_slack_project_settings_ui(origin, settings=None)
            load_settings(core, origin, settings=None)
            load_custom_channel_settings(core, origin)
            return

        settings.create_slack_custom_channel_ui(origin, settings=None)
        load_custom_channel_settings(core, origin)

    else:
        settings.create_slack_project_settings_ui(origin, settings=None)
        load_settings(core, origin, settings=None)
        load_custom_channel_settings(core, origin)
