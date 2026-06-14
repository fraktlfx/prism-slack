import os


class Prism_Slack_Variables(object):
    def __init__(self, core: object, plugin: object):
        self.version = "v2.1.2"
        self.pluginName = "Slack"
        self.pluginType = "Custom"
        self.platforms = ["Windows", "Darwin", "Linux"]
        self.pluginDirectory = os.path.abspath(
            os.path.dirname(os.path.dirname(__file__))
        )
