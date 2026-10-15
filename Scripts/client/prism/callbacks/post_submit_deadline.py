#    @err_catcher(name=__name__)
#     def postSubmit_Deadline(self, origin, jobResult, jobInfos, pluginInfos, arguments):
#         """
#         This callback is triggered after a Deadline job is submitted. It checks if the job submission was successful and if the Slack Publish option is enabled for the current state.
#         If so, it gathers necessary information about the job and its dependencies, prepares the data to be sent to Slack, and submits a new Deadline job that will execute a script to publish the information to Slack.

#         Args:
#             origin (Any): The source of the callback, not used in this function.
#             jobResult (str): The result string returned from the Deadline job submission, used to extract the job ID for dependencies.
#             jobInfos (dict): A dictionary containing information about the submitted job, such as its name, batch, output filename, pool, group, machine limit, and initial status.
#             pluginInfos (dict): A dictionary containing information about the plugin, not used in this function.
#             arguments (dict): A dictionary of additional arguments, not used in this function.
#         """

#         # ---------
#         # Grab the users current state from the State Manager
#         # ---------

#         state = getattr(self.core.getStateManager(), "curExecutedState", None)
#         if not state:
#             logger.warning(
#                 "Could not retrieve current state from State Manager. Exiting postSubmit_Deadline callback."
#             )
#             return

#         from pprint import pprint

#         pprint(f"State: {state}")
#         pprint(f"Origin: P{origin}")
#         pprint(f"Job Result: {jobResult}")
#         pprint(f"Job Info: {jobInfos}")
#         pprint(f"Plugin Info: {pluginInfos}")
#         pprint(f"Arguments: {arguments}")

#         # ---------
#         # Check if Slack Publish is enabled for the current state. If it is and the publish checkbox is checked, proceed with gathering information and submitting the Slack publish job to Deadline.
#         # If not, exit the function.
#         # ---------
#         if state.gb_slack.isChecked() and state.chb_slackPublish.isChecked():
#             logger.info(
#                 "# --------- postSubmit_Deadline callback triggered. Retrieving current state and checking if Slack Publish is enabled for this job. --------- #"
#             )

#             # ---------
#             # Exit if no Slack user is configured
#             # ---------
#             if not API(self.core).get_prism_slack_user_id():
#                 logger.warning(
#                     "No Slack user configured. Please set up your Slack user in the Prism Slack plugin settings to enable Slack publishing."
#                 )
#                 return

#             # ---------
#             # Retrieve Deadline Job Information
#             # ---------
#             job = jobInfos.get("Name")
#             if state.cb_master.currentText() != "Don't Update Master":
#                 batch = jobInfos.get("BatchName")
#                 logger.info(
#                     f"Job is part of batch '{batch}', will set Slack publish job to be part of the same batch."
#                 )
#             else:
#                 batch = ""

#             try:
#                 output_raw = jobInfos.get("OutputFilename0")
#                 if not output_raw:
#                     logger.warning(
#                         "No Deadline output filename found in 'OutputFilename0'. Skipping Slack publish job submission."
#                     )
#                     return

#                 output = str(output_raw).replace("\\", "/").strip()
#                 if not output:
#                     logger.warning(
#                         "Deadline output filename is empty after normalization. Skipping Slack publish job submission."
#                     )
#                     return

#                 logger.info(f"Retrieved job output filename: {output}")
#             except Exception:
#                 logger.exception(
#                     "Failed to resolve Deadline output filename. Skipping Slack publish job submission."
#                 )
#                 return

#             # ---------
#             # Exit if the job is one of these types
#             # ---------
#             exit_names = ["_updateMaster", "_publishToSlack", "_cleanup", "_export"]
#             for name in exit_names:
#                 if name in jobInfos.get("Name"):
#                     return

#             logger.info(
#                 f"[Slack] Job '{job}' passed initial checks for Slack publishing. Proceeding with gathering information and submitting Slack publish job to Deadline."
#             )

#             # ---------
#             # Determine Job Dependencies
#             # ---------
#             if self.core.getPlugin("MediaExtension") is not None:
#                 if self.core.appPlugin.pluginName == "Nuke":
#                     import nuke

#                     node = nuke.thisNode()
#                     for name, knob in node.knobs().items():
#                         if knob.Class() == "Tab_Knob":
#                             print(f"Internal name: '{name}', Label: '{knob.label()}'")

#                     versioninfo = os.path.join(
#                         os.path.dirname(os.path.dirname(output)), "versioninfo.json"
#                     )

#                 if hasattr(state, "chb_mediaConversion") and state.chb_mediaConversion.isChecked():
#                     if output:
#                         os.environ["JOB_OUTPUT_PATH"] = output

#                     if "_mediaConversion" in jobInfos.get("Name"):
#                         id = re.search(r"JobID=([a-f0-9]+)", jobResult)
#                         if id:
#                             job_dependency = id.group(1)

#                         output = os.getenv("JOB_OUTPUT_PATH", default="")
#                         if not output:
#                             logger.warning(
#                                 "Could not resolve media conversion output path from JOB_OUTPUT_PATH. Skipping Slack publish job submission."
#                             )
#                             return
#                         job = job.replace("_mediaConversion", "")
#                     else:
#                         return
#                 else:
#                     job_dependency = self.core.getPlugin("Deadline").getJobIdFromSubmitResult(
#                         jobResult
#                     )
#             else:
#                 job_dependency = self.core.getPlugin("Deadline").getJobIdFromSubmitResult(jobResult)

#             versioninfo = os.path.join(os.path.dirname(os.path.dirname(output)), "versioninfo.json")

#             # ---------
#             # Prepare State Data for Slack Publish
#             # ---------
#             state_data = {
#                 "project": API(self.core).get_current_project(),
#                 "range_type": state.cb_rangeType.currentText(),
#                 "comments": state.te_slackComments.toPlainText(),
#                 "state_type": "render",
#                 "ui": "DL",
#                 "fps": str(self.core.getConfig("globals", "fps", configPath=self.core.prismIni)),
#                 "app": self.core.appPlugin.pluginName,
#                 "versioninfo": versioninfo,
#             }

#             # --------- Start / End Frame for State Data ---------
#             if state.cb_rangeType.currentText() == "Custom":
#                 state_data["start_frame"] = state.sp_rangeStart.text()
#                 state_data["end_frame"] = state.sp_rangeEnd.text()

#             else:
#                 state_data["start_frame"] = state.l_rangeStart.text()
#                 state_data["end_frame"] = state.l_rangeEnd.text()

#             # --------- Determine if Media Conversion is needed ---------
#             if self.core.getPlugin("MediaExtension") is not None:
#                 state_data["convert_media"] = state.chb_mediaConversion.isChecked()
#                 state_data["converted_extension"] = state.cb_mediaConversion.currentText().lower()
#             else:
#                 state_data["convert_media"] = None
#                 state_data["converted_extension"] = None

#             # --------- Determine whether to send Approval buttons to Slack ---------
#             if API(self.core).get_server_approvals() is True:
#                 state_data["status"] = state.cb_approvals.currentText()

#             # --------- Retrieve the script that will be executed on Deadline job ---------
#             code = deadline_submission_script(self.core, output, state_data)

#             # --------- Retrieve the Deadline plugin ---------
#             dl = self.core.getPlugin("Deadline")

#             # --------- Submit the Deadline job ---------
#             _ = dl.submitPythonJob(
#                 code=code,
#                 jobName=job + "_publishToSlack",
#                 jobPrio=80,
#                 jobPool=jobInfos.get("Pool"),
#                 jobSndPool=jobInfos.get("SecondaryPool"),
#                 jobGroup=jobInfos.get("Group"),
#                 jobTimeOut=180,
#                 jobMachineLimit=jobInfos.get("MachineLimit"),
#                 frames="1",
#                 suspended=jobInfos.get("InitialStatus") == "Suspended",
#                 jobDependencies=[job_dependency],
#                 jobBatchName=batch,
#                 args=arguments,
#                 state=state,
#             )

#         return
