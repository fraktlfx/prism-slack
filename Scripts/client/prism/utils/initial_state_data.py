import os
from client.prism.api import API
from .ae_utils import get_aftereffects_frame_data


def get_state_data(
    core: object,
    state: dict[str, str],
    output: str,
    ui: str,
    state_type: str,
) -> dict:
    """
    Gather initial state data for Slack publishing from the core application and the state manager.

    Args:
        core (object): The core application object.
        state (dict[str, str]): The state manager containing user selections and settings.
        output (str): The output path of the render.
        state_type (str): The type of state data being gathered (e.g., "pb" for playblast or "render" for render).
    Returns:
        dict: A dictionary containing the initial state data for Slack publishing.
    """
    app = core.appPlugin.pluginName

    # -----------
    # Construct the initial state data dictionary with common information
    # -----------
    state_data = {
        "project": API(core).get_current_project(),
        "state_type": state_type,
        "ui": ui,
        "fps": str(core.getConfig("globals", "fps", configPath=core.prismIni)),
        "app": app,
    }

    if app == "AfterEffects":
        state_data["versioninfo"] = os.path.join(
            os.path.dirname(output), "versioninfo.json"
        ).replace("\\", "/")
        state_data["comments"] = state.te_slackComments.toPlainText()

        frame_data = get_aftereffects_frame_data(output)
        state_data["range_type"] = frame_data.get("range_type")
        state_data["start_frame"] = str(frame_data.get("start_frame"))
        state_data["end_frame"] = str(frame_data.get("end_frame"))

        state_data["convert_media"] = None
        state_data["converted_extension"] = None

        return state_data

    else:
        # ----------
        # For other applications (primarily 3D Applications), the versioninfo.json is typically located one directory up from the output
        # ----------

        if state_type == "pb":
            state_data["versioninfo"] = os.path.join(
                os.path.dirname(output), "versioninfo.json"
            ).replace("\\", "/")
            state_data["extension"] = state.cb_formats.currentText()

        else:
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
        else:
            state_data["convert_media"] = None
            state_data["converted_extension"] = None

        return state_data
