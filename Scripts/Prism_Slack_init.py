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


import client.slack.api as slack_api
from client.prism.api import API
from client.prism.utils.publish_to_slack import PublishToSlack
from prism_plugin_utils.Prism_Slack_externalAccess_Functions import (
    Prism_Slack_externalAccess_Functions,
)
from prism_plugin_utils.Prism_Slack_Functions import Prism_Slack_Functions
from prism_plugin_utils.Prism_Slack_Variables import Prism_Slack_Variables


class Prism_Slack(
    Prism_Slack_Variables,
    Prism_Slack_Functions,
    Prism_Slack_externalAccess_Functions,
    PublishToSlack,
    API,
):
    def __init__(self, core):
        self.core = core
        Prism_Slack_Variables.__init__(self, core, self)

        Prism_Slack_Functions.__init__(self, core, self)
        Prism_Slack_externalAccess_Functions.__init__(self, core, self)
        PublishToSlack.__init__(self, core)
        API.__init__(self, core)

        for func in slack_api.__all__:
            setattr(self, func, getattr(slack_api, func))
