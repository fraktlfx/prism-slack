from prism_slack.client.slack.publish import Publish
from prism_slack.client.prism.utils import (
    get_state_data,
    check_publish_options,
    check_deadline_option,
    log_and_print,
)


# Handle output result after playblast
def postPlayblast(core: object, **kwargs: dict[str, str]):
    """
    Begin the publishing process to Slack after a playblast is completed.

    Args:
        core (object): The core application object.
        **kwargs (dict[str, str]): Additional keyword arguments containing state and settings.
    """
    log_and_print(20, "[PostPlayblast] postPlayblast callback triggered.")
    app = core.appPlugin.pluginName
    state = kwargs.get("state")

    if not check_publish_options(core, state, app, option="publish"):
        return

    output: str = kwargs.get("outputpath", "").replace("\\", "/")

    state_data = get_state_data(core=core, state=state, output=output, ui="SM", state_type="pb")

    if check_deadline_option(core, state):
        return

    log_and_print(20, f"Publishing to Slack with output: {output} and state data: {state_data}")

    Publish(core).publish_to_slack(output, state_data)
