import os
import sys
import types

scripts = os.path.dirname(__file__)
root = os.path.dirname(scripts)
modules = os.path.join(root, "PythonLibs")

for path in (modules, root):
    if path not in sys.path:
        sys.path.insert(0, path)

namespace = sys.modules.get("prism_slack")
if namespace is None:
    namespace = types.ModuleType("prism_slack")
    namespace.__path__ = [scripts]
    sys.modules["prism_slack"] = namespace

from prism_slack.client.prism.utils.logging import setup_logging
import prism_slack.client.slack.api as slack_api
from prism_slack.client.prism.api import API
from prism_slack.client.slack.publish import Publish
from prism_slack.prism_plugin_utils.Prism_Slack_externalAccess_Functions import (
    Prism_Slack_externalAccess_Functions,
)
from prism_slack.prism_plugin_utils.Prism_Slack_Functions import Prism_Slack_Functions
from prism_slack.prism_plugin_utils.Prism_Slack_Variables import Prism_Slack_Variables


class Prism_Slack(
    Prism_Slack_Variables,
    Prism_Slack_Functions,
    Prism_Slack_externalAccess_Functions,
    Publish,
    API,
):
    def __init__(self, core):
        self.core = core

        setup_logging(log_dir=os.path.dirname(self.core.configs.getConfigPath("user")), level=20)
        Prism_Slack_Variables.__init__(self, core, self)

        Prism_Slack_Functions.__init__(self, core, self)
        Prism_Slack_externalAccess_Functions.__init__(self, core, self)
        Publish.__init__(self, core)
        API.__init__(self, core)

        for func in slack_api.__all__:
            setattr(self, func, getattr(slack_api, func))
