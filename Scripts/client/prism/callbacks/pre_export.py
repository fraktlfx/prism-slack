import os
from prism_slack.client.prism.utils import check_publish_options, log_and_print
from prism_slack.client.slack.notifications import notify_before_publish


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

    if not check_publish_options(core=core, state=state, app=app, option="notification"):
        return

    notify_user = state.cb_slackUserPool.currentText()

    try:
        if hasattr(state, "l_taskName") and state.l_taskName:
            product = state.l_taskName.text()
        elif (
            hasattr(state, "l_departmentLayer")
            and state.l_departmentLayer.isVisible()
            and state.l_departmentLayer
        ):
            product = state.l_departmentLayer.text()
        elif hasattr(state, "l_product") and state.l_product.isVisible() and state.l_product:
            product = state.l_product.text()
        else:
            print("Failed to get product name from state. Defaulting to the Task Name instead.")
            product = os.environ.get("PRISM_TASK", "Unknown Product")

    except Exception:
        print("Failed to get product name from state. Defaulting to the Task Name instead.")
        product = os.environ.get("PRISM_TASK", "Unknown Product")

    notify_before_publish(core=core, notify_user=notify_user, product=product)
