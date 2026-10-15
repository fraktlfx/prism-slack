import os
import re
from functools import partial

from prism_slack.client.prism.api import API
from prism_slack.client.prism.callbacks.media_player_context_menu_requested import (
    mediaPlayerContextMenuRequested,
)
from prism_slack.client.prism.callbacks.on_state_startup import onStateStartup
from prism_slack.client.prism.callbacks.on_write_gizmo_create import onWriteGizmoCreated
from prism_slack.client.prism.callbacks.on_nuke_node_created import onNukeNodeCreated
from prism_slack.client.prism.callbacks.post_playblast import postPlayblast
from prism_slack.client.prism.callbacks.post_render import postRender
from prism_slack.client.prism.callbacks.pre_export import preExport
from prism_slack.client.prism.callbacks.pre_playblast import prePlayblast
from prism_slack.client.prism.callbacks.pre_render import preRender
from prism_slack.client.prism.callbacks.pre_submit_deadline import preSubmit_Deadline
from prism_slack.client.prism.callbacks.on_after_effects_render_dlg_created import (
    onAfterEffectsRenderDlgCreated,
)
from prism_slack.client.prism.utils.deadline_submission import deadline_submission_script
from prism_slack.client.prism.utils import log_and_print, check_publish_options
from prism_slack.client.slack.slack_config import SlackConfig
from prism_slack.server.controls import ServerControls

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


class Prism_Slack_Functions(object):
    def __init__(self, core: object, plugin: object):
        self.core = core
        self.plugin = plugin
        self.config = SlackConfig(self.core)

        self.slack_config = self.config.load_config(mode="studio")
        self.config.check_slack_studio_options(self.slack_config)

        self.core.registerCallback(
            "mediaPlayerContextMenuRequested",
            partial(mediaPlayerContextMenuRequested, self.core),
            plugin=self.plugin,
            priority=30,
        )
        self.core.registerCallback(
            "onStateStartup",
            partial(onStateStartup, self.core),
            plugin=self,
            priority=15,
        )
        self.core.registerCallback(
            "onWriteGizmoCreated",
            partial(onWriteGizmoCreated, self.core),
            plugin=self,
            priority=15,
        )
        self.core.registerCallback(
            "onNukeNodeCreated",
            partial(onNukeNodeCreated, self.core),
            plugin=self,
            priority=15,
        )
        self.core.registerCallback(
            "postPlayblast", partial(postPlayblast, self.core), plugin=self, priority=15
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
            "preExport", partial(preExport, self.core), plugin=self, priority=15
        )
        self.core.registerCallback(
            "onAfterEffectsRenderDlgCreated",
            partial(onAfterEffectsRenderDlgCreated, self.core),
            plugin=self,
            priority=15,
        )
        self.core.registerCallback(
            "preSubmit_Deadline",
            partial(preSubmit_Deadline, self.core),
            plugin=self,
            priority=15,
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
    def postSubmit_Deadline(self, origin, jobResult, jobInfos, pluginInfos, arguments):
        """
        This callback is triggered after a Deadline job is submitted. It checks if the job submission was successful and if the Slack Publish option is enabled for the current state.
        If so, it gathers necessary information about the job and its dependencies, prepares the data to be sent to Slack, and submits a new Deadline job that will execute a script to publish the information to Slack.

        Args:
            origin (Any): The source of the callback, not used in this function.
            jobResult (str): The result string returned from the Deadline job submission, used to extract the job ID for dependencies.
            jobInfos (dict): A dictionary containing information about the submitted job, such as its name, batch, output filename, pool, group, machine limit, and initial status.
            pluginInfos (dict): A dictionary containing information about the plugin, not used in this function.
            arguments (dict): A dictionary of additional arguments, not used in this function.
        """
        app = self.core.appPlugin.pluginName
        log_and_print(20, "\n################################\n" * 3)

        # Guard values are initialized up front because callback branches can return
        # without preparing Slack publish payload data.
        output = ""
        state_data = None
        job = ""
        batch = ""
        job_dependency = None
        deadline_state = None
        should_submit = False

        # ---------
        # Grab the users current state from the State Manager
        # ---------

        if app == "AfterEffects":
            state = self.core.appPlugin.dlg_render
            if (
                state is not None
                and state.gb_slack.isChecked()
                and state.chb_slackPublish.isChecked()
            ):
                self.core.popup(
                    "The Slack plugin currently does not support After Effects Deadline submissions."
                )
                log_and_print(
                    30,
                    "User attempted to submit to Deadline from After Effects, which is not currently supported.",
                )
                return

        elif app == "Nuke":
            try:
                import nuke
            except Exception:
                return None

            try:
                write_node = pluginInfos.get("WriteNode")
                if write_node is None:
                    write_node = os.getenv("NUKE_WRITE_NODE", default="")
                os.environ["NUKE_WRITE_NODE"] = write_node
            except Exception:
                print(
                    "Write node information not found in pluginInfos for Nuke Deadline submission."
                )

            # --------- Retrieve Job Information ---------
            from pprint import pprint

            pprint(f"jobInfos: {jobInfos}")
            job = jobInfos.get("Name")
            if jobInfos.get("BatchName") != "":
                batch = jobInfos.get("BatchName")
            else:
                batch = ""

            try:
                output: str = jobInfos.get("OutputFilename0").replace("\\", "/")

            except Exception:
                output = ""

            # --------- Exit if the job is one of these types ---------
            exit_names = ["_updateMaster", "_publishToSlack", "_cleanup", "_export"]
            for name in exit_names:
                if name in jobInfos.get("Name"):
                    print(
                        f"Job name contains '{name}', skipping Slack Deadline post-submit actions."
                    )
                    return

            node = nuke.toNode(write_node)

            # --------- Determine Job Dependencies ---------
            if self.core.getPlugin("MediaExtension") is not None:
                if bool(node["media_conversion_use"].value()):
                    if output is not None and output != "":
                        os.environ["JOB_OUTPUT_PATH"] = output
                        os.environ["NUKE_WRITE_NODE"] = write_node

                    if "_mediaConversion" in jobInfos.get("Name"):
                        id = re.search(r"JobID=([a-f0-9]+)", jobResult)
                        if id:
                            job_dependency = id.group(1)

                        output = os.getenv("JOB_OUTPUT_PATH", default="")
                        write_node = os.getenv("NUKE_WRITE_NODE", default="")
                        job = job.replace("_mediaConversion", "")

                    else:
                        return
                else:
                    job_dependency = self.core.getPlugin(
                        "Deadline"
                    ).getJobIdFromSubmitResult(jobResult)
            else:
                job_dependency = self.core.getPlugin(
                    "Deadline"
                ).getJobIdFromSubmitResult(jobResult)

            extension = os.path.splitext(output)[1].lower()

            if extension in [".mov", ".mp4", ".avi"]:
                output = output.replace(".####", "")

            state_data = {
                "project": API(self.core).get_current_project(),
                "state_type": "render",
                "ui": "DL",
                "fps": str(
                    self.core.getConfig("globals", "fps", configPath=self.core.prismIni)
                ),
                "app": app,
                "user": API(self.core).get_prism_slack_user_id(),
            }
            state_data["versioninfo"] = os.path.join(
                os.path.dirname(output), "versioninfo.json"
            ).replace("\\", "/")

            state_data["comments"] = node["slack_comments"].value()

            if API(self.core).get_server_approvals():
                status_map = {0: "Work in Progress", 1: "Request Review"}
                state_data["status"] = status_map.get(
                    int(node["slack_approvals"].getValue()), ""
                )

            if self.core.getPlugin("MediaExtension") is not None:
                state_data["convert_media"] = bool(node["media_conversion_use"].value())
                state_data["converted_extension"] = node[
                    "media_conversion_preset"
                ].value()
            else:
                state_data["convert_media"] = None
                state_data["converted_extension"] = None

            try:
                state = getattr(self.core.getStateManager(), "curExecutedState", None)
                if not state:
                    return

                state_data["range_type"] = state.cb_rangeType.currentText()

                if state.cb_rangeType.currentText() == "Custom":
                    state_data["start_frame"] = state.sp_rangeStart.text()
                    state_data["end_frame"] = state.sp_rangeEnd.text()
                else:
                    state_data["start_frame"] = state.l_rangeStart.text()
                    state_data["end_frame"] = state.l_rangeEnd.text()

            except Exception as exc:
                log_and_print(
                    30,
                    f"Could not determine Nuke frame range for output '{output}': {exc}",
                )
                state_data["range_type"] = "Custom"
                state_data["start_frame"] = ""
                state_data["end_frame"] = ""

            if "slack_publish" not in node.knobs():
                print(
                    "Slack knobs not found on node, skipping Slack Deadline post-submit actions."
                )
                return

            if node["slack_publish"].value():
                print(
                    "Slack Publish is enabled for this node, preparing to submit Slack Deadline job..."
                )
                state = node
                batch = jobInfos.get("BatchName") or ""
                print(
                    f"Collected job information: Job Name: {job}, Batch: {batch}, Output: {output}"
                )
                deadline_state = getattr(
                    self.core.getStateManager(), "curExecutedState", None
                )
                if deadline_state is None or not hasattr(deadline_state, "uuid"):
                    log_and_print(
                        30,
                        "Could not resolve Prism state context for Nuke Deadline submission; skipping Slack Deadline post-submit actions.",
                    )
                    return

                # state_data = self._get_initial_state_data(self.core, node, output)
                print(f"Initial state data collected: {state_data}")
                job_dependency = self._retrieve_dependency(
                    jobInfos, jobResult, node, output
                )
                print(f"Retrieved job dependency: {job_dependency}")
                if job_dependency is None:
                    return

                log_and_print(
                    20, f"[NUKE] Publishing to Slack: {output}\n with data {state_data}"
                )
                should_submit = True

        else:
            state = getattr(self.core.getStateManager(), "curExecutedState", None)
            deadline_state = state
            if not state:
                return

            from pprint import pprint

            pprint(f"jobInfos: {jobInfos}")

            if state.gb_slack.isChecked() and state.chb_slackPublish.isChecked():
                # --------- Exit if no Slack user is configured ---------
                if not API(self.core).get_prism_slack_user_id():
                    return

                # --------- Retrieve Job Information ---------
                job = jobInfos.get("Name")
                if state.cb_master.currentText() != "Don't Update Master":
                    batch = jobInfos.get("BatchName")
                else:
                    batch = ""

                try:
                    output: str = jobInfos.get("OutputFilename0")
                    output = output.replace("\\", "/")
                    if output is None:
                        return
                except Exception:
                    output = ""

                # --------- Exit if the job is one of these types ---------
                exit_names = ["_updateMaster", "_publishToSlack", "_cleanup", "_export"]
                for name in exit_names:
                    if name in jobInfos.get("Name"):
                        return

                # --------- Determine Job Dependencies ---------
                if self.core.getPlugin("MediaExtension") is not None:
                    if hasattr(state, "chb_mediaConversion"):
                        if state.chb_mediaConversion.isChecked():
                            if output is not None and output != "":
                                os.environ["JOB_OUTPUT_PATH"] = output

                            if "_mediaConversion" in jobInfos.get("Name"):
                                id = re.search(r"JobID=([a-f0-9]+)", jobResult)
                                if id:
                                    job_dependency = id.group(1)

                                output = os.getenv("JOB_OUTPUT_PATH", default="")
                                job = job.replace("_mediaConversion", "")

                            else:
                                return
                        else:
                            job_dependency = self.core.getPlugin(
                                "Deadline"
                            ).getJobIdFromSubmitResult(jobResult)
                    else:
                        job_dependency = self.core.getPlugin(
                            "Deadline"
                        ).getJobIdFromSubmitResult(jobResult)
                else:
                    job_dependency = self.core.getPlugin(
                        "Deadline"
                    ).getJobIdFromSubmitResult(jobResult)

                versioninfo = os.path.join(
                    os.path.dirname(os.path.dirname(output)), "versioninfo.json"
                )

                # --------- Prepare State Data for Slack Publish ---------
                state_data = {
                    "project": API(self.core).get_current_project(),
                    "range_type": state.cb_rangeType.currentText(),
                    "publish_to_slack": state.chb_slackPublish.isChecked(),
                    "comments": state.te_slackComments.toPlainText(),
                    "state_type": "render",
                    "ui": "DL",
                    "fps": str(
                        self.core.getConfig(
                            "globals", "fps", configPath=self.core.prismIni
                        )
                    ),
                    "app": self.core.appPlugin.pluginName,
                    "versioninfo": versioninfo,
                    "user": API(self.core).get_prism_slack_user_id(),
                }

                # --------- Start / End Frame for State Data ---------
                if state.cb_rangeType.currentText() == "Custom":
                    state_data["start_frame"] = state.sp_rangeStart.text()
                    state_data["end_frame"] = state.sp_rangeEnd.text()

                else:
                    state_data["start_frame"] = state.l_rangeStart.text()
                    state_data["end_frame"] = state.l_rangeEnd.text()

                # --------- Determine if Media Conversion is needed ---------
                if self.core.getPlugin("MediaExtension") is not None:
                    if state.className != "LOP Render":
                        state_data["convert_media"] = (
                            state.chb_mediaConversion.isChecked()
                        )
                        state_data["converted_extension"] = (
                            state.cb_mediaConversion.currentText().lower()
                        )
                    else:
                        state_data["convert_media"] = None
                        state_data["converted_extension"] = None
                else:
                    state_data["convert_media"] = None
                    state_data["converted_extension"] = None

                # --------- Determine whether to send Approval buttons to Slack ---------
                if API(self.core).get_server_approvals() is True:
                    state_data["status"] = state.cb_approvals.currentText()

                should_submit = True

        if not should_submit or state_data is None:
            return

        code = deadline_submission_script(self.core, output, state_data)

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
            state=deadline_state,
        )

        return

    def _get_initial_state_data(self, core: object, state: object, output: str) -> dict:
        app = self.core.appPlugin.pluginName
        state_data = {
            "project": API(core).get_current_project(),
            "state_type": "render",
            "ui": "DL",
            "fps": str(core.getConfig("globals", "fps", configPath=core.prismIni)),
            "app": app,
            "user": API(self.core).get_prism_slack_user_id(),
        }

        if app == "Nuke":
            state_data["versioninfo"] = os.path.join(
                os.path.dirname(output), "versioninfo.json"
            ).replace("\\", "/")

            state_data["comments"] = state["slack_comments"].value()

            if API(core).get_server_approvals():
                status_map = {0: "Work in Progress", 1: "Request Review"}
                state_data["status"] = status_map.get(
                    int(state["slack_approvals"].getValue()), ""
                )

            if core.getPlugin("MediaExtension") is not None:
                state_data["convert_media"] = bool(
                    state["media_conversion_use"].value()
                )
                state_data["converted_extension"] = state[
                    "media_conversion_preset"
                ].value()
            else:
                state_data["convert_media"] = None
                state_data["converted_extension"] = None

            try:
                state = getattr(self.core.getStateManager(), "curExecutedState", None)
                if not state:
                    return

                state_data["range_type"] = state.cb_rangeType.currentText()

                if state.cb_rangeType.currentText() == "Custom":
                    state_data["start_frame"] = state.sp_rangeStart.text()
                    state_data["end_frame"] = state.sp_rangeEnd.text()
                else:
                    state_data["start_frame"] = state.l_rangeStart.text()
                    state_data["end_frame"] = state.l_rangeEnd.text()

            except Exception as exc:
                log_and_print(
                    30,
                    f"Could not determine Nuke frame range for output '{output}': {exc}",
                )
                state_data["range_type"] = "Custom"
                state_data["start_frame"] = ""
                state_data["end_frame"] = ""

            return state_data

        else:
            # ----------
            # For other applications (primarily 3D Applications), the versioninfo.json is typically located one directory up from the output
            # ----------
            state_data["versioninfo"] = os.path.join(
                os.path.dirname(os.path.dirname(output)), "versioninfo.json"
            ).replace("\\", "/")

            state_data["range_type"] = state.cb_rangeType.currentText()
            state_data["comments"] = state.te_slackComments.toPlainText()

            if state.cb_rangeType.currentText() == "Custom":
                state_data["start_frame"] = state.sp_rangeStart.text()
                state_data["end_frame"] = state.sp_rangeEnd.text()
            else:
                state_data["start_frame"] = state.l_rangeStart.text()
                state_data["end_frame"] = state.l_rangeEnd.text()

            if core.getPlugin("MediaExtension") is not None:
                state_data["convert_media"] = state.chb_mediaConversion.isChecked()
                state_data["converted_extension"] = (
                    state.cb_mediaConversion.currentText().lower()
                )
                log_and_print(
                    20,
                    f"Media conversion settings - Convert: {state_data['convert_media']}, Extension: {state_data['converted_extension']}",
                )

            else:
                state_data["convert_media"] = None
                state_data["converted_extension"] = None
                log_and_print(
                    20,
                    "Media Extension plugin not loaded, applying None to conversion settings.",
                )

            if API(core).get_server_approvals():
                state_data["status"] = state.cb_approvals.currentText()

            return state_data

    def _retrieve_dependency(
        self, jobInfos: dict, jobResult: str, state: object, output: str
    ) -> str | None:
        job = jobInfos.get("Name")
        app = self.core.appPlugin.pluginName

        exit_names = ["_updateMaster", "_publishToSlack", "_cleanup", "_export"]

        for name in exit_names:
            if name in jobInfos.get("Name"):
                return

        if self.core.getPlugin("MediaExtension") is None:
            log_and_print(
                20,
                "Media Extension plugin not detected, proceeding without media conversion...",
            )
            return self.core.getPlugin("Deadline").getJobIdFromSubmitResult(jobResult)

        if app == "Nuke":
            log_and_print(
                20, "Nuke job detected, checking media conversion settings..."
            )
            if bool(state["media_conversion_use"].value()) is False:
                log_and_print(
                    20,
                    "Media conversion not enabled for this job, proceeding without media conversion...",
                )
                return self.core.getPlugin("Deadline").getJobIdFromSubmitResult(
                    jobResult
                )

            log_and_print(
                20, "Media conversion enabled for this job, checking settings..."
            )
            if output is not None:
                os.environ["JOB_OUTPUT_PATH"] = output
                log_and_print(
                    20, f"Set JOB_OUTPUT_PATH environment variable to: {output}"
                )

            if "_mediaConversion" in jobInfos.get("Name"):
                log_and_print(20, f"Job name: {jobInfos.get('Name')}")
                id = re.search(r"JobID=([a-f0-9]+)", jobResult)
                log_and_print(20, f"Job id: {id}")
                if id:
                    job_dependency = id.group(1)

                output = os.getenv("JOB_OUTPUT_PATH")
                job = job.replace("_mediaConversion", "")
                log_and_print(
                    20,
                    f"Media conversion job detected, job dependency set to: {job_dependency}",
                )

                return job_dependency

            return

        else:
            if (
                hasattr(state, "chb_mediaConversion")
                and state.chb_mediaConversion.isChecked()
            ):
                log_and_print(
                    20, "Media conversion enabled for this job, checking settings..."
                )
                if output is not None:
                    os.environ["JOB_OUTPUT_PATH"] = output
                    log_and_print(
                        20, f"Set JOB_OUTPUT_PATH environment variable to: {output}"
                    )

                if "_mediaConversion" in jobInfos.get("Name"):
                    id = re.search(r"JobID=([a-f0-9]+)", jobResult)
                    if id:
                        job_dependency = id.group(1)

                    output = os.getenv("JOB_OUTPUT_PATH")
                    job = job.replace("_mediaConversion", "")
                    log_and_print(
                        20,
                        f"Media conversion job detected, job dependency set to: {job_dependency}",
                    )
                    return job_dependency

                else:
                    return
            else:
                log_and_print(
                    20,
                    "Media Extesion not being used for this job, proceeding without media conversion...",
                )
                return self.core.getPlugin("Deadline").getJobIdFromSubmitResult(
                    jobResult
                )
