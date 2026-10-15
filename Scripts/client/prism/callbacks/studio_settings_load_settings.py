from prism_slack.client.prism.ui.settings_ui import SettingsUI
from prism_slack.client.prism.ui import SlackStudioPathNotFound
from prism_slack.client.prism.ui.load_settings import load_settings

from qtpy.QtWidgets import QWidget


def studioSettings_loadSettings(core: object, origin: QWidget, settings: object):
    """
    Load the Slack UI in the studio settings window.

    Args:
        core (object): The core application object.
        origin (QWidget): The origin QWidget (studio settings window).
        settings (object): The settings UI object.
    """
    settings = SettingsUI(core)

    if core.getPlugin("Studio").getStudioConfigPath() is None:
        SlackStudioPathNotFound().exec_()
        return

    if core.getPlugin("Studio").isStudioActive() is False:
        return

    settings.create_slack_studio_settings_ui(origin, settings)
    load_settings(core, origin, settings)
