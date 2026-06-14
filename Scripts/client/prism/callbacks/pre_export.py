from client.prism.utils import log_and_print, check_publish_options
from client.slack.notifications import notify_before_publish


def preExport(core: object, **kwargs: dict[str, str]):
    """
    Pre-export callback to notify a Slack user about an upcoming export.

    Args:
        core (object): The core application object
        **kwargs (dict[str, str]): Additional keyword arguments
    """
    log_and_print(20, "[PreExport] preExport callback triggered.")

    app = core.appPlugin.pluginName

    state = kwargs.get("state", None)

    if not check_publish_options(
        core=core, state=state, app=app, option="notification"
    ):
        return

    notify_user = state.cb_slackUserPool.currentText()
    product = state.l_taskName.text()

    notify_before_publish(core=core, notify_user=notify_user, product=product)
