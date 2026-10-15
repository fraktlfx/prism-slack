from prism_slack.client.prism.api import API
from .logging import log_and_print


def check_publish_options(core: object, state: object, app: str, option: str) -> bool:
    """
    Check if the necessary options for publishing to Slack are enabled.

    Args:
        core (object): The core application object.
        state (object): The state objects containing the UI elements.
        app (str): The name of the application (e.g., "AfterEffects", "Nuke").
        option (str): The specific option to check ("publish" or "notification").
    Returns:
        bool: True if the necessary options for publishing to Slack are enabled, False otherwise.
    """
    if app == "Nuke":
        node_name = state.name() if hasattr(state, "name") else "<unknown>"
        knob_names = list(state.knobs().keys()) if hasattr(state, "knobs") else []
        log_and_print(20, f"[NUKE] Node: {node_name} | Knobs: {knob_names}")

        # print the name of the state node and its state knobs and their output for debugging
        log_and_print(
            20,
            f"[NUKE] Checking publish options. State knobs: {[f'{knob.name()}: {knob.value()}' for knob in state.knobs().values()]}",
        )

        if "slack_publish" not in state.knobs():
            log_and_print(20, "[NUKE] Slack knobs not found on the node. Skipping Slack publish.")
            return False

        if option == "publish":
            if not state["slack_publish"].value():
                log_and_print(
                    20, "[NUKE] Slack publish option is not enabled. Skipping Slack publish."
                )
                return False

        if option == "notification":
            if not state["slack_notify"].value():
                log_and_print(
                    20,
                    "[NUKE] Slack notification option is not enabled. Skipping Slack notification.",
                )
                return False

    else:
        if not state:
            log_and_print(20, f"[{app.upper()}] No state found in postRender callback.")
            return False

        if not hasattr(state, "gb_slack"):
            log_and_print(
                20, f"[{app.upper()}] Slack UI elements not found in postRender state object."
            )
            return False

        if not state.gb_slack.isChecked():
            log_and_print(
                20, f"[{app.upper()}] Slack options are disabled. Skipping Slack publish."
            )
            return False

        if option == "publish" and not state.chb_slackPublish.isChecked():
            log_and_print(
                20, f"[{app.upper()}] Slack publish option is not enabled. Skipping Slack publish."
            )
            return False

        if option == "notification" and not state.chb_slackNotify.isChecked():
            log_and_print(
                20,
                f"[{app.upper()}] Slack notification option is not enabled. Skipping Slack notification.",
            )
            return False

        if not API(core).get_prism_slack_user_id():
            log_and_print(
                20,
                f"[{app.upper()}] User not authenticated with Slack. Prompting user to authenticate in Prism Settings.",
            )
            core.popup(
                f"[{app.upper()}] You'll need to use the Sign in with Slack option in the Prism settings before being able to Publish."
            )
            return False

    return True


def check_deadline_option(core: object, state: object) -> bool:
    """
    Check if the Deadline submit option is enabled, which should prevent Slack publishing.

    Args:
        core (object): The core application object.
        state (object): The state objects containing the UI elements.
    Returns:
        bool: True if the Deadline submit option is enabled, False otherwise.
    """
    if core.getPlugin("Deadline") and hasattr(state, "gb_submit"):
        if state.gb_submit.isChecked():
            log_and_print(
                20,
                f"[{core.appPlugin.pluginName.upper()}] Deadline submit checked, skipping Slack publish.",
            )
            return True

        else:
            log_and_print(
                20,
                f"[{core.appPlugin.pluginName.upper()}] Deadline submit not checked, proceeding with Slack publish.",
            )
            return False

    return False
