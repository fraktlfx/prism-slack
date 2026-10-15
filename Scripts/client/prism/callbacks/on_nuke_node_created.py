from prism_slack.client.prism.api import API
from prism_slack.client.prism.utils import log_and_print
from prism_slack.client.slack.api.get import get_channel_id, get_channel_users, get_studio_users


def onNukeNodeCreated(core: object, **kwargs: dict[str, str]):
    """
    Callback function triggered when a new node is created in Nuke. This function checks if the created node has a "slack_publish" knob, and if so, it sets the default value of that knob to True.
    This ensures that any new nodes created with the intention of being published to Slack will have the publish option enabled by default.

    Args:
        core (object): The core application object, used to access plugins and other functionality.
        **kwargs (dict[str, str]): Additional keyword arguments that may be passed by the callback system, not used in this function.
    """
    try:
        import nuke
    except Exception as e:
        log_and_print(40, f"Failed to import nuke module: {e}")
        return

    node = nuke.thisNode()

    if "Write" not in node.Class():
        return

    if "slack_div" in node.knobs():
        return

    try:
        slack_label_knob = nuke.Text_Knob("slack_div", "")
        slack_header = nuke.Text_Knob("slack_header", "", "<b>Slack</b>")
        slack_label_knob.setFlag(nuke.STARTLINE)
        node.addKnob(slack_label_knob)
        node.addKnob(slack_header)

        publish_knob = nuke.Boolean_Knob("slack_publish", "Publish to Slack")
        publish_knob.setFlag(nuke.STARTLINE)
        node.addKnob(publish_knob)

        notify_knob = nuke.Boolean_Knob("slack_notify", "Notify Artist")
        notify_knob.setFlag(nuke.STARTLINE)
        node.addKnob(notify_knob)

        spacing = nuke.Text_Knob("pad", "", "    ")
        spacing.clearFlag(nuke.STARTLINE)
        node.addKnob(spacing)

        notify_artists_knob = nuke.Enumeration_Knob("slack_notify_artists", "", [])
        notify_artists_knob.clearFlag(nuke.STARTLINE)
        node.addKnob(notify_artists_knob)
        _populate_notify_artists(core, node)

        if API(core).get_server_approvals():
            approvals_knob = nuke.Enumeration_Knob(
                "slack_approvals", "Status", ["Work in Progress", "Request Review"]
            )
            approvals_knob.setFlag(nuke.STARTLINE)
            node.addKnob(approvals_knob)

        comments_knob = nuke.Multiline_Eval_String_Knob("slack_comments", "Comments (optional)")
        node.addKnob(comments_knob)

    except Exception as e:
        log_and_print(40, f"Failed to set up Slack knobs on the Prism Write Gizmo: {e}")


def _populate_notify_artists(core: object, node: object):
    """
    Populate the notify artists dropdown in the Write Gizmo Slack tab.

    Args:
        core (object): The core application object.
        node (object): The Write Gizmo node.
    """

    try:
        access_token = API(core).get_access_token()
        proj = API(core).get_current_project()
        channel_id = get_channel_id(access_token, proj)

        notify_user_pool = API(core).get_notify_user_pool().lower()

        users = []
        if notify_user_pool == "studio":
            users = get_studio_users(core=core)

        elif notify_user_pool == "channel":
            members = get_channel_users(access_token, channel_id)
            users = [member["display_name"] for member in members]

        notify_artists_knob = node.knob("slack_notify_artists")
        if notify_artists_knob:
            notify_artists_knob.setValues(users)
        else:
            log_and_print(10, "Notify artists knob not found on the node.")

    except Exception as e:
        log_and_print(40, f"Failed to populate notify artists: {e}")
