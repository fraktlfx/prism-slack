import os
from functools import partial

from prism_slack.client.prism.api import API
from prism_slack.client.prism.utils import log_and_print
from prism_slack.client.prism.callbacks.project_browser_load_ui import (
    projectBrowser_loadUI,
)
from prism_slack.client.prism.callbacks.project_settings_load_ui import (
    projectSettings_loadUI,
)
from prism_slack.client.prism.callbacks.studio_settings_load_settings import (
    studioSettings_loadSettings,
)
from prism_slack.client.prism.callbacks.tray_context_menu_requested import (
    TrayContextMenuRequested,
)
from prism_slack.client.prism.callbacks.user_settings_load_ui import userSettings_loadUI
from prism_slack.client.slack.slack_config import SlackConfig
from PrismUtils.Decorators import err_catcher_plugin as err_catcher


class Prism_Slack_externalAccess_Functions(object):
    def __init__(self, core: object, plugin: object):
        self.core = core
        self.plugin = plugin

        self.core.registerCallback("onPluginsLoaded", self.onPluginsLoaded, plugin=self)

        self.core.registerCallback(
            "userSettings_loadUI",
            partial(userSettings_loadUI, self.core),
            plugin=self,
        )

        if self._check_project_loaded() is False:
            pass
        else:
            self.tray_handler = TrayContextMenuRequested(self.core)

            self.core.registerCallback(
                "trayContextMenuRequested",
                self.tray_handler,
                plugin=plugin,
            )

    @err_catcher(name=__name__)
    def onPluginsLoaded(self):
        if not self.core.uiAvailable:
            pass

        elif self._check_project_loaded() is False:
            log_and_print(10, "No project loaded")
            pass

        else:
            if self.core.getPlugin("ExecutionGraph") is not None:
                self._add_execution_graph_nodepaths_to_env()
                self._add_execution_graph_graph_folders_to_env()

        if API(self.core).is_studio_loaded() is not None:
            self.core.registerCallback(
                "studioSettings_loadSettings",
                partial(studioSettings_loadSettings, self.core),
                plugin=self,
            )
            self.core.registerCallback(
                "projectSettings_loadUI",
                partial(projectSettings_loadUI, self.core),
                plugin=self,
            )
        else:
            self.core.registerCallback(
                "projectSettings_loadUI",
                partial(projectSettings_loadUI, self.core),
                plugin=self,
            )

        self.core.registerCallback(
            "projectBrowser_loadUI",
            partial(projectBrowser_loadUI, self.core),
            plugin=self,
        )

        self.core.registerCallback(
            "userSettings_loadUI",
            partial(userSettings_loadUI, self.core),
            plugin=self,
        )

    def _check_project_loaded(self) -> bool:
        import json

        try:
            user_config_path = SlackConfig(self.core).get_user_config_path()
            with open(user_config_path, "r") as f:
                project_name = json.load(f)["globals"]["current project"]

            if project_name is None or project_name == "":
                return False

            return True

        except Exception:
            return False

    def _add_execution_graph_nodepaths_to_env(self):
        eg_nodepaths_name = "PRISM_EG_NODEDEF_PATHS"

        eg_nodes_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "Resources",
            "NodeDefs",
            "slack_nodedefs.json",
        )

        eg_nodepaths_env = os.getenv(eg_nodepaths_name)
        log_and_print(10, f"Current PRISM_EG_NODEDEF_PATHS: {eg_nodepaths_env}")

        if eg_nodepaths_env is None:
            os.environ[eg_nodepaths_name] = eg_nodes_path
            log_and_print(10, "Created and Added EG NodeDef path: " + eg_nodes_path)

        else:
            eg_nodepaths = eg_nodepaths_env.split(os.pathsep)

            if eg_nodes_path not in eg_nodepaths:
                eg_nodepaths.append(eg_nodes_path)
                os.environ[eg_nodepaths_name] = os.pathsep.join(eg_nodepaths)
                log_and_print(
                    10,
                    "Added EG NodeDef to environment variable with path: "
                    + eg_nodes_path,
                )

            else:
                log_and_print(10, "EG NodeDef path already set.")

    def _add_execution_graph_graph_folders_to_env(self):
        eg_graphs_name = "PRISM_EG_GRAPH_FOLDERS"

        eg_graphs_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "Resources",
            "NodeGraphs",
        )

        eg_graphs_env = os.getenv(eg_graphs_name)

        if eg_graphs_env is None:
            os.environ[eg_graphs_name] = eg_graphs_path
            log_and_print(10, "Created and Added EG Graph path: " + eg_graphs_path)

        else:
            eg_graphs = eg_graphs_env.split(os.pathsep)

            if eg_graphs_path not in eg_graphs:
                eg_graphs.append(eg_graphs_path)
                os.environ[eg_graphs_name] = os.pathsep.join(eg_graphs)
                log_and_print(
                    10,
                    "Added EG Graph to environment variable with path: "
                    + eg_graphs_path,
                )

            else:
                log_and_print(10, "EG Graph path already set.")
