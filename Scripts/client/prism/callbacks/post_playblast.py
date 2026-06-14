from Scripts.client.prism.api import API
from Scripts.client.slack.publish import Publish
from Scripts.client.prism.utils import (
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

    state = kwargs.get("state", None)

    if not check_publish_options(core, state, app, option="publish"):
        return

    output = kwargs.get("outputpath", None).replace("\\", "/")

    state_data = get_state_data(
        core=core, state=state, output=output, ui="SM", state_type="pb"
    )

    if check_deadline_option(core, state):
        return

    log_and_print(
        20, f"Publishing to Slack with output: {output} and state data: {state_data}"
    )
    Publish(core).publish_to_slack(
        output, state_data, prism_user=API(core).get_prism_slack_username()
    )
