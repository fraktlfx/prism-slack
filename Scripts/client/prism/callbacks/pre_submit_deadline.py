from typing import Any

from prism_slack.client.prism.utils import check_publish_options, log_and_print
from prism_slack.client.slack.notifications import notify_before_publish

from qtpy.QtWidgets import QWidget


def preSubmit_Deadline(
    core: object, origin: QWidget, jobInfos: Any, pluginInfos: Any, arguments: Any
):
    """
    Pre-submit callback for Deadline to notify a Slack user about an upcoming submission.
    """
    log_and_print(20, "[Deadline] preSubmit_Deadline callback triggered.")
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
        return
        state = getattr(core.getStateManager(), "curExecutedState", None)

        if not check_publish_options(core=core, state=state, app=app, option="notification"):
            return

        notify_user = state.cb_slackUserPool.currentText()

        if app == "AfterEffects":
            product = state.e_identifier.text()
        else:
            product = state.l_taskName.text()

        notify_before_publish(core=core, notify_user=notify_user, product=product)
