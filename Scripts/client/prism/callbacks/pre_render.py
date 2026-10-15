from prism_slack.client.prism.utils import check_publish_options, log_and_print
from prism_slack.client.slack.notifications import notify_before_publish


def preRender(core: object, **kwargs: dict[str, str]):
    """
    Pre-render callback to notify a Slack user about an upcoming render.

    Args:
        core (object): The core application object
        **kwargs (dict[str, str]): Additional keyword arguments
    """
    log_and_print(20, "[PreRender] preRender callback triggered.")
    app = core.appPlugin.pluginName

    if app == "Nuke":
        import nuke

        node = nuke.thisNode()

        if not check_publish_options(core=core, state=node, app=app, option="notification"):
            return

        notify_user = node["slack_notify_artists"].value()

        product = node["identifier"].value()

        notify_before_publish(core=core, notify_user=notify_user, product=product)

    else:
        if app == "AfterEffects":
            state = core.appPlugin.dlg_render
        else:
            state = kwargs.get("state", None)

        if not check_publish_options(core=core, state=state, app=app, option="notification"):
            return

        notify_user = state.cb_slackUserPool.currentText()

        if app == "AfterEffects":
            product = state.e_identifier.text()
        else:
            product = state.l_taskName.text()

        notify_before_publish(core=core, notify_user=notify_user, product=product)
