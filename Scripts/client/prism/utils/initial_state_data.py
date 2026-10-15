import os
from prism_slack.client.prism.api import API
from .determine_frame_range import determine_frame_range
from .ae_utils import get_aftereffects_frame_data


def get_state_data(core: object, state: object, output: str, ui: str, state_type: str) -> dict:
    """
    Gather initial state data for Slack publishing from the core application and the state manager.

    Args:
        core (object): The core application object.
        state (object): The state manager containing user selections and settings.
        output (str): The output path of the render.
        ui (str): The user interface context, e.g. "SM" for State Manager.
        state_type (str): The type of state, e.g. "pb" for playblast

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

    state_data["versioninfo"] = _get_versioninfo_path(output, state_type)

    if app == "Nuke":
        state_data["comments"] = state["slack_comments"].value()
    else:
        state_data["comments"] = state.te_slackComments.toPlainText()

    if app not in ["Nuke", "AfterEffects"] and state_type == "pb":
        state_data["extension"] = state.cb_formats.currentText()

    state_data.update(_get_start_end_frames(state, output, state_data, app))
    state_data.update(_get_convert_media(core, state, app))
    state_data.update(_get_server_approvals_status(core, state, app))

    return state_data


def _get_versioninfo_path(output: str, state_type: str) -> str:
    """
    Get the path to the versioninfo.json file based on the output path and state type.

    Args:
        output (str): The output path of the render.
        state_type (str): The type of state, e.g. "pb" for playblast.
        app (str): The name of the application, e.g. "AfterEffects", "Nuke", etc.

    Returns:
        str: The path to the versioninfo.json file.
    """
    if state_type == "render":
        return os.path.join(os.path.dirname(os.path.dirname(output)), "versioninfo.json").replace(
            "\\", "/"
        )
    else:
        return os.path.join(os.path.dirname(output), "versioninfo.json").replace("\\", "/")


def _get_start_end_frames(state: object, output: str, state_data: dict, app: str) -> dict:
    """
    Get the start and end frames based on the state manager settings.

    Args:
        state (object): The state manager containing user selections and settings.
        output (str): The output path of the render.
        state_data (dict): The state data dictionary to be updated with start and end frame information.
        app (str): The name of the application, e.g. "AfterEffects", "Nuke", etc.
    Returns:
        dict: A dictionary containing the range type, start frame, and end frame.
    """
    if app == "Nuke":
        frame_range = determine_frame_range(output)
        state_data["range_type"] = frame_range["range_type"]
        state_data["start_frame"] = str(frame_range["start_frame"])
        state_data["end_frame"] = str(frame_range["end_frame"])
        return state_data

    if app == "AfterEffects":
        frame_data = get_aftereffects_frame_data(output)
        state_data["range_type"] = frame_data.get("range_type")
        state_data["start_frame"] = str(frame_data.get("start_frame"))
        state_data["end_frame"] = str(frame_data.get("end_frame"))
        return state_data

    state_data["range_type"] = state.cb_rangeType.currentText()

    if state.cb_rangeType.currentText() == "Custom":
        state_data["start_frame"] = state.sp_rangeStart.text()
        state_data["end_frame"] = state.sp_rangeEnd.text()
    else:
        state_data["start_frame"] = state.l_rangeStart.text()
        state_data["end_frame"] = state.l_rangeEnd.text()

    return state_data


def _get_convert_media(core: object, state: object, app: str) -> dict:
    """
    Get the media conversion settings based on the state manager settings.

    Args:
        core (object): The core application object.
        state (object): The state manager containing user selections and settings.
        app (str): The name of the application, e.g. "AfterEffects", "Nuke", etc.

    Returns:
        dict: A dictionary containing the convert_media boolean and converted_extension string.
    """
    if core.getPlugin("MediaExtension") is None:
        return {"convert_media": None, "converted_extension": None}

    if app == "Nuke":
        convert_media = bool(state["media_conversion_use"].value())
        converted_extension = state["media_conversion_preset"].value()
        return {"convert_media": convert_media, "converted_extension": converted_extension}

    if app == "AfterEffects":
        return {"convert_media": None, "converted_extension": None}

    if getattr(state, "className", "") == "LOP Render":
        return {"convert_media": None, "converted_extension": None}

    convert_media = state.chb_mediaConversion.isChecked()
    converted_extension = state.cb_mediaConversion.currentText().lower()
    return {"convert_media": convert_media, "converted_extension": converted_extension}


def _get_server_approvals_status(core: object, state: object, app: str) -> dict:
    """
    Get the server approvals status from the state manager settings and update the state data accordingly.

    Args:
        core (object): The core application object.
        state (object): The state manager containing user selections and settings.

    Returns:
        dict: A dictionary containing the status string if server approvals are enabled, otherwise None.
    """

    if not API(core).get_server_approvals():
        return {"status": None}

    if app == "Nuke":
        status_map = {0: "Work in Progress", 1: "Request Review"}
        status = status_map.get(int(state["slack_approvals"].getValue()), "")
        return {"status": status}

    status = state.cb_approvals.currentText()
    return {"status": status}
