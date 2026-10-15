import os


def deadline_submission_script(core: object, output: str, state_data: dict):
    """
    Generate a Deadline submission script for Slack upload.
    Args:
        core (object): The core application object.
        output (str): The output file path.
        state_data (dict): The state data containing settings from the state manager

    Return:
        code: Submission used to submit content from Deadline to Slack.
    """

    root = os.path.join(core.prismRoot, "Scripts")
    root = root.replace("\\", "/")
    project = state_data["project"]

    code = f"""
import os
import sys
sys.path.append("{root}")
import PrismCore

pcore = PrismCore.create(prismArgs=["noUI", "{project}"])

slack = pcore.getPlugin('Slack')

slack.publish_to_slack(r"{output}", {state_data})
"""

    return code
