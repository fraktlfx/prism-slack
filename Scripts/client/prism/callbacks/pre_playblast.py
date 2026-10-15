from prism_slack.client.prism.utils import check_publish_options, check_deadline_option, log_and_print
from prism_slack.client.slack.notifications import notify_before_publish


def prePlayblast(core: object, **kwargs: dict[str, str]):
    """
    Pre-playblast callback to notify a Slack user about an upcoming playblast.

    Args:
        core (object): The core application object
        **kwargs (dict[str, str]): Additional keyword arguments
    """
    log_and_print(20, "[PrePlayblast] prePlayblast callback triggered.")
    app = core.appPlugin.pluginName

    state = kwargs.get("state", None)

    if not check_publish_options(core=core, state=state, app=app, option="notification"):
        return

    if check_deadline_option(core, state):
        return

    notify_user = state.cb_slackUserPool.currentText()

    product = state.l_taskName.text()

    notify_before_publish(core=core, notify_user=notify_user, product=product)
