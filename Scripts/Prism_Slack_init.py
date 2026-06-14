import os
import sys

scripts = os.path.dirname(__file__)
root = os.path.dirname(scripts)
modules = os.path.join(root, "PythonLibs")

if root not in sys.path:
    sys.path.append(root)
if scripts not in sys.path:
    sys.path.append(scripts)
if modules not in sys.path:
    sys.path.append(modules)

from client.prism.utils.logging import setup_logging
from client.prism.api import API
import client.slack.api as slack_api
from client.slack.publish import Publish
from prism_plugin_utils.Prism_Slack_externalAccess_Functions import (
    Prism_Slack_externalAccess_Functions,
)
from prism_plugin_utils.Prism_Slack_Functions import Prism_Slack_Functions
from prism_plugin_utils.Prism_Slack_Variables import Prism_Slack_Variables


class Prism_Slack(
    Prism_Slack_Variables,
    Prism_Slack_Functions,
    Prism_Slack_externalAccess_Functions,
    Publish,
    API,
):
    def __init__(self, core):
        self.core = core
        setup_logging(
            log_dir=os.path.dirname(self.core.configs.getConfigPath("user")), level=20
        )

        Prism_Slack_Variables.__init__(self, core, self)
        Prism_Slack_Functions.__init__(self, core, self)
        Prism_Slack_externalAccess_Functions.__init__(self, core, self)

        Publish.__init__(self, core)
        API.__init__(self, core)

        for func in slack_api.__all__:
            setattr(self, func, getattr(slack_api, func))
