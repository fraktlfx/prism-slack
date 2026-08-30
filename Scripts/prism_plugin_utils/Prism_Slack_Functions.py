import os
import re
from functools import partial

from prism_slack.client.prism.api import API
from prism_slack.server.controls import ServerControls
from prism_slack.client.slack.slack_config import SlackConfig
from prism_slack.client.prism.callbacks.media_player_context_menu_requested import (
    mediaPlayerContextMenuRequested,
)
from prism_slack.client.prism.callbacks.on_after_effects_render_dlg_created import (
    onAfterEffectsRenderDlgCreated,
)
from prism_slack.client.prism.callbacks.on_state_startup import onStateStartup
from prism_slack.client.prism.callbacks.post_playblast import postPlayblast
from prism_slack.client.prism.callbacks.post_render import postRender
from prism_slack.client.prism.callbacks.pre_render import preRender
from prism_slack.client.prism.callbacks.pre_export import preExport
from prism_slack.client.prism.callbacks.pre_playblast import prePlayblast
from prism_slack.client.prism.utils import (
    deadline_submission_script,
    get_state_data,
    log_and_print,
    resolve_aftereffects_output,
)

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


class Prism_Slack_Functions(object):
    def __init__(self, core: object, plugin: object):
        self.core = core
        self.plugin = plugin
        print(f"Type of self.plugin: {type(self.plugin)}")
        self.config = SlackConfig(self.core)

        self.slack_config = self.config.load_config(mode="studio")
        self.config.check_slack_studio_options(self.slack_config)

        log_and_print(20, "Registering Slack plugin callbacks...")
        self.core.registerCallback(
            "mediaPlayerContextMenuRequested",
            partial(mediaPlayerContextMenuRequested, self.core),
            plugin=self.plugin,
            priority=30,
        )
        self.core.registerCallback(
            "onAfterEffectsRenderDlgCreated",
            partial(onAfterEffectsRenderDlgCreated, self.core),
            plugin=self,
            priority=15,
        )
        self.core.registerCallback(
            "onStateStartup",
            partial(onStateStartup, self.core),
            plugin=self,
            priority=15,
        )
        self.core.registerCallback(
            "postPlayblast", partial(postPlayblast, self.core), plugin=self, priority=15
        )
        self.core.registerCallback(
            "preExport", partial(preExport, self.core), plugin=self, priority=15
        )
        self.core.registerCallback(
            "postRender", partial(postRender, self.core), plugin=self, priority=15
        )
        self.core.registerCallback(
            "preRender", partial(preRender, self.core), plugin=self, priority=15
        )
        self.core.registerCallback(
            "prePlayblast", partial(prePlayblast, self.core), plugin=self, priority=15
        )
        self.core.registerCallback(
            "postSubmit_Deadline", self.postSubmit_Deadline, plugin=self, priority=15
        )

    # Sets the plugin as active
    @err_catcher(name=__name__)
    def isActive(self):
        return True

    @err_catcher(name=__name__)
    def start_bolt_server(self):
        ServerControls(self.core).start_server()

    @err_catcher(name=__name__)
    def stop_bolt_server(self):
        ServerControls(self.core).stop_server()

    @err_catcher(name=__name__)
    def reset_bolt_server_status(self):
        ServerControls(self.core).reset_server_status()

    @err_catcher(name=__name__)
    def postSubmit_Deadline(
        self,
        origin: object,
        jobResult: str,
        jobInfos: dict,
        pluginInfos: dict,
        arguments: list,
    ):
        state = getattr(self.core.getStateManager(), "curExecutedState", None)
        if not state:
            log_and_print(20, "State object not found in preExport callback.")
            return

        if not hasattr(state, "gb_slack"):
            log_and_print(
                20, "Slack notification UI elements not found in state object."
            )
            return

        if not state.gb_slack.isChecked() and not state.chb_slackPublish.isChecked():
            log_and_print(
                20, "Slack notifications are disabled. Skipping Slack notification."
            )
            return

        job = jobInfos.get("Name")

        if state.cb_master.currentText() != "Don't Update Master":
            batch = jobInfos.get("BatchName")
        else:
            batch = ""

        try:
            output = jobInfos.get("OutputFilename0")
            output = output.replace("\\", "/")
            if output is None:
                return

        except Exception:
            output = None

        exit_names = ["_updateMaster", "_publishToSlack", "_cleanup", "_export"]

        for name in exit_names:
            if name in jobInfos.get("Name"):
                return

        media_extension = self.core.getPlugin("MediaExtension")

        if media_extension is None:
            job_dependency = self.core.getPlugin("Deadline").getJobIdFromSubmitResult(
                jobResult
            )

        else:
            if (
                hasattr(state, "chb_mediaConversion")
                and state.chb_mediaConversion.isChecked()
            ):
                if output is not None:
                    os.environ["JOB_OUTPUT_PATH"] = output

                if "_mediaConversion" in jobInfos.get("Name"):
                    id = re.search(r"JobID=([a-f0-9]+)", jobResult)
                    if id:
                        job_dependency = id.group(1)

                    output = os.getenv("JOB_OUTPUT_PATH")
                    job = job.replace("_mediaConversion", "")

                else:
                    return
            else:
                job_dependency = self.core.getPlugin(
                    "Deadline"
                ).getJobIdFromSubmitResult(jobResult)

        prism_user = API(self.core).get_prism_slack_username()

        state_data = get_state_data(
            core=self.core, state=state, output=output, ui="DL", state_type="render"
        )

        code = deadline_submission_script(self.core, output, state_data, prism_user)

        dl = self.core.getPlugin("Deadline")

        dl.submitPythonJob(
            code=code,
            jobName=job + "_publishToSlack",
            jobPrio=80,
            jobPool=jobInfos.get("Pool"),
            jobSndPool=jobInfos.get("SecondaryPool"),
            jobGroup=jobInfos.get("Group"),
            jobTimeOut=180,
            jobMachineLimit=jobInfos.get("MachineLimit"),
            frames="1",
            suspended=jobInfos.get("InitialStatus") == "Suspended",
            jobDependencies=[job_dependency],
            jobBatchName=batch,
            args=arguments,
            state=state,
        )

        return
