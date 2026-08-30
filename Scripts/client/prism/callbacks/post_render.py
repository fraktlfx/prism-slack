from prism_slack.client.prism.api import API
from prism_slack.client.slack.publish import Publish
from prism_slack.client.prism.utils import (
    resolve_aftereffects_output,
    get_state_data,
    log_and_print,
    check_publish_options,
    check_deadline_option,
)


# Handle the output result after rendering
def postRender(core: object, **kwargs: dict[str, str]):
    """
    Begin the publishing process to Slack after a render is completed.

    Args:
        core (object): The core application object.
        **kwargs (dict[str, str]): Additional keyword arguments containing state and settings.
    """
    log_and_print(20, "[PostRender] postRender callback triggered.")

    app = core.appPlugin.pluginName

    prism_user = API(core).get_prism_slack_username()

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

        state_data = get_state_data(
            core=core, state=state, output=output, ui="SM", state_type="render"
        )

    else:
        state = kwargs.get("state", None)

        if not check_publish_options(core, state, app, option="publish"):
            return

        output = kwargs.get("settings", None)["outputName"].replace("\\", "/")

        state_data = get_state_data(
            core=core, state=state, output=output, ui="SM", state_type="render"
        )

        if check_deadline_option(core, state):
            return

        log_and_print(
            20,
            f"Publishing to Slack with output: {output} and state data: {state_data}",
        )

    Publish(core).publish_to_slack(output, state_data, prism_user)
