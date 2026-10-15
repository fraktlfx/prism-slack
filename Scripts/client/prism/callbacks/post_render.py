from prism_slack.client.slack.publish import Publish

from prism_slack.client.prism.utils import (
    log_and_print,
    get_state_data,
    check_publish_options,
    check_deadline_option,
    resolve_aftereffects_output,
)


def postRender(core: object, **kwargs: dict[str, str]):
    """
    Begin the publishing process to Slack after a render is completed.

    Args:
        core (object): The core application object.
        **kwargs (dict[str, str]): Additional keyword arguments containing state and settings.
    """
    log_and_print(20, "[PostRender] postRender callback triggered.")
    state = kwargs.get("state", None)
    app = core.appPlugin.pluginName

    if app == "AfterEffects":
        state = core.appPlugin.dlg_render

        if not check_publish_options(core, state, app, option="publish"):
            return

        output = kwargs.get("outputpath", {})

        output = resolve_aftereffects_output(core, output)

        if output is None:
            log_and_print(20, f"[AE] Output path could not be resolved: {output}")
            core.popup(f"Output path does not exist: {output}")
            return

        state_data = get_state_data(core, state, output, ui="SM", state_type="render")

        log_and_print(20, f"[AE] Initial state data for After Effects: {state_data}")

    elif app == "Nuke":
        try:
            import nuke
        except ImportError:
            log_and_print(40, "Nuke module not found. Ensure this plugin is running within Nuke.")
            return

        node = nuke.thisNode()
        log_and_print(20, f"[NUKE] Post-render callback triggered for node: {node.name()}")

        if not check_publish_options(core, node, app, option="publish"):
            return

        output = kwargs.get("settings", {})["outputName"].replace("\\", "/")

        state_data = get_state_data(core, node, output, ui="SM", state_type="render")

        log_and_print(20, f"[NUKE] Publishing to Slack: {output}\n with data {state_data}")

    else:
        if not check_publish_options(core, state, app, option="publish"):
            return

        if check_deadline_option(core, state):
            return

        output = kwargs.get("settings", {})["outputName"].replace("\\", "/")

        state_data = get_state_data(core, state, output, ui="SM", state_type="render")

        log_and_print(20, f"Publishing to Slack with output: {output} and state data: {state_data}")

    Publish(core).publish_to_slack(output, state_data)
